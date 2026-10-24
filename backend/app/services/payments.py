"""Payment initiation and callback handling (simulation + sandbox adapter)."""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.payment import PaymentIntent, PaymentCallback, PaymentStatus
from app.services.ledger import LedgerService, DuplicateIdempotencyError

settings = get_settings()


class PaymentError(Exception):
    pass


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)

    async def initiate_deposit(
        self,
        *,
        user_id: uuid.UUID,
        amount_cents: int,
        phone: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        description: str = "Wallet top-up",
    ) -> PaymentIntent:
        if amount_cents < 100:  # min 1 KES
            raise PaymentError("Minimum deposit is 1 KES")
        if amount_cents > 150_000_00:  # 150,000 KES safety limit
            raise PaymentError("Amount exceeds maximum allowed for simulation")

        if idempotency_key:
            existing = await self.db.execute(
                select(PaymentIntent).where(PaymentIntent.idempotency_key == idempotency_key)
            )
            found = existing.scalar_one_or_none()
            if found:
                return found

        external_ref = f"MTAA{uuid.uuid4().hex[:12].upper()}"
        intent = PaymentIntent(
            user_id=user_id,
            amount_cents=amount_cents,
            currency="KES",
            status=PaymentStatus.PENDING.value,
            provider="mpesa_sim" if settings.daraja_mode == "simulation" else "mpesa_sandbox",
            external_reference=external_ref,
            phone=phone,
            description=description,
            idempotency_key=idempotency_key,
        )
        self.db.add(intent)
        await self.db.flush()

        if settings.daraja_mode == "simulation":
            # Immediately complete in simulation mode for local dev convenience
            # (still goes through proper ledger path)
            await self._complete_intent(intent)
        else:
            # Placeholder for real Daraja STK push initiation
            intent.status = PaymentStatus.PROCESSING.value
            await self.db.flush()

        return intent

    async def _complete_intent(self, intent: PaymentIntent) -> None:
        if intent.status == PaymentStatus.COMPLETED.value:
            return
        try:
            entry = await self.ledger.credit_deposit(
                user_id=intent.user_id,
                amount_cents=intent.amount_cents,
                external_reference=intent.external_reference,
                description=intent.description or "Simulated deposit",
                idempotency_key=f"pay:{intent.external_reference}",
            )
            intent.journal_entry_id = entry.id
            intent.status = PaymentStatus.COMPLETED.value
            intent.completed_at = datetime.now(timezone.utc)
        except DuplicateIdempotencyError:
            intent.status = PaymentStatus.COMPLETED.value
            intent.completed_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def handle_callback(
        self,
        *,
        external_reference: str,
        payload: dict,
        provider: str = "mpesa_sim",
    ) -> PaymentIntent:
        # Record raw callback first
        cb = PaymentCallback(
            external_reference=external_reference,
            provider=provider,
            payload=json.dumps(payload),
            processed=False,
        )
        self.db.add(cb)
        await self.db.flush()

        result = await self.db.execute(
            select(PaymentIntent).where(PaymentIntent.external_reference == external_reference)
        )
        intent = result.scalar_one_or_none()
        if not intent:
            cb.processed = True
            cb.processing_result = "unknown_reference"
            await self.db.flush()
            raise PaymentError("Unknown payment reference")

        cb.payment_intent_id = intent.id

        if intent.status == PaymentStatus.COMPLETED.value:
            cb.processed = True
            cb.processing_result = "already_completed"
            await self.db.flush()
            return intent

        # Validate success indicators from payload (simulation accepts result_code == 0)
        result_code = payload.get("ResultCode", payload.get("result_code"))
        if result_code is not None and str(result_code) not in ("0", "00"):
            intent.status = PaymentStatus.FAILED.value
            cb.processed = True
            cb.processing_result = "failed"
            await self.db.flush()
            return intent

        await self._complete_intent(intent)
        cb.processed = True
        cb.processing_result = "completed"
        await self.db.flush()
        return intent
