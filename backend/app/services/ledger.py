"""Double-entry ledger service.

All amounts are integer cents. Every posted entry is balanced.
Concurrency-safe balance updates via SELECT FOR UPDATE.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Sequence, Tuple

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.ledger import Account, JournalEntry, JournalLine, AccountType
from app.models.user import User


class LedgerError(Exception):
    """Base ledger error."""


class InsufficientFundsError(LedgerError):
    pass


class UnbalancedEntryError(LedgerError):
    pass


class DuplicateIdempotencyError(LedgerError):
    def __init__(self, existing_entry: JournalEntry):
        self.existing_entry = existing_entry
        super().__init__("Duplicate idempotency key")


class LedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_user_wallet(self, user_id: uuid.UUID) -> Account:
        code = f"user_wallet:{user_id}"
        result = await self.db.execute(select(Account).where(Account.code == code))
        account = result.scalar_one_or_none()
        if account:
            return account
        account = Account(
            code=code,
            name=f"User Wallet {user_id}",
            account_type=AccountType.USER_WALLET.value,
            user_id=user_id,
            currency="KES",
            balance_cents=0,
        )
        self.db.add(account)
        await self.db.flush()
        return account

    async def get_system_account(self, account_type: AccountType, code: str, name: str) -> Account:
        result = await self.db.execute(select(Account).where(Account.code == code))
        account = result.scalar_one_or_none()
        if account:
            return account
        account = Account(
            code=code,
            name=name,
            account_type=account_type.value,
            user_id=None,
            currency="KES",
            balance_cents=0,
        )
        self.db.add(account)
        await self.db.flush()
        return account

    async def _lock_account(self, account_id: uuid.UUID) -> Account:
        result = await self.db.execute(
            select(Account).where(Account.id == account_id).with_for_update()
        )
        account = result.scalar_one()
        return account

    async def post_entry(
        self,
        *,
        reference: str,
        description: str,
        entry_type: str,
        lines: Sequence[Tuple[uuid.UUID, str, int, Optional[str]]],
        # (account_id, side, amount_cents, memo)
        idempotency_key: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
        related_user_id: Optional[uuid.UUID] = None,
        metadata: Optional[dict] = None,
    ) -> JournalEntry:
        if idempotency_key:
            existing = await self.db.execute(
                select(JournalEntry).where(JournalEntry.idempotency_key == idempotency_key)
            )
            found = existing.scalar_one_or_none()
            if found:
                raise DuplicateIdempotencyError(found)

        total_debit = 0
        total_credit = 0
        for _, side, amount, _ in lines:
            if amount <= 0:
                raise LedgerError("Line amount must be positive")
            if side == "debit":
                total_debit += amount
            elif side == "credit":
                total_credit += amount
            else:
                raise LedgerError(f"Invalid side: {side}")

        if total_debit != total_credit:
            raise UnbalancedEntryError(
                f"Unbalanced entry: debits={total_debit} credits={total_credit}"
            )

        entry = JournalEntry(
            reference=reference,
            description=description,
            entry_type=entry_type,
            idempotency_key=idempotency_key,
            created_by=created_by,
            related_user_id=related_user_id,
            metadata_json=json.dumps(metadata) if metadata else None,
            posted_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        await self.db.flush()

        for account_id, side, amount, memo in lines:
            account = await self._lock_account(account_id)
            line = JournalLine(
                entry_id=entry.id,
                account_id=account_id,
                side=side,
                amount_cents=amount,
                memo=memo,
            )
            self.db.add(line)

            # Update cached balance
            # User wallets are liabilities: credit increases balance, debit decreases
            if account.account_type == AccountType.USER_WALLET.value:
                if side == "credit":
                    account.balance_cents += amount
                else:
                    if account.balance_cents < amount:
                        raise InsufficientFundsError(
                            f"Insufficient funds on {account.code}: "
                            f"have {account.balance_cents}, need {amount}"
                        )
                    account.balance_cents -= amount
            else:
                # For asset/clearing accounts we still track a running balance
                if side == "debit":
                    account.balance_cents += amount
                else:
                    account.balance_cents -= amount

            account.updated_at = datetime.now(timezone.utc)

        await self.db.flush()
        return entry

    async def transfer(
        self,
        *,
        from_user_id: uuid.UUID,
        to_user_id: uuid.UUID,
        amount_cents: int,
        description: str = "Internal transfer",
        idempotency_key: Optional[str] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> JournalEntry:
        if amount_cents <= 0:
            raise LedgerError("Transfer amount must be positive")
        if from_user_id == to_user_id:
            raise LedgerError("Cannot transfer to self")

        from_wallet = await self.get_or_create_user_wallet(from_user_id)
        to_wallet = await self.get_or_create_user_wallet(to_user_id)

        # Lock both accounts in consistent order to avoid deadlocks
        first, second = sorted([from_wallet.id, to_wallet.id], key=str)
        await self._lock_account(first)
        await self._lock_account(second)

        # Re-fetch after lock
        from_wallet = await self._lock_account(from_wallet.id)
        to_wallet = await self._lock_account(to_wallet.id)

        if from_wallet.balance_cents < amount_cents:
            raise InsufficientFundsError(
                f"Insufficient funds: have {from_wallet.balance_cents}, need {amount_cents}"
            )

        ref = f"TRF-{uuid.uuid4().hex[:16].upper()}"
        return await self.post_entry(
            reference=ref,
            description=description,
            entry_type="transfer",
            lines=[
                (from_wallet.id, "debit", amount_cents, "Transfer out"),
                (to_wallet.id, "credit", amount_cents, "Transfer in"),
            ],
            idempotency_key=idempotency_key,
            created_by=created_by or from_user_id,
            related_user_id=to_user_id,
            metadata={"from_user": str(from_user_id), "to_user": str(to_user_id)},
        )

    async def credit_deposit(
        self,
        *,
        user_id: uuid.UUID,
        amount_cents: int,
        external_reference: str,
        description: str = "M-Pesa deposit (simulated)",
        idempotency_key: Optional[str] = None,
    ) -> JournalEntry:
        """Credit a user's wallet from the external/mpesa suspense account."""
        if amount_cents <= 0:
            raise LedgerError("Deposit amount must be positive")

        wallet = await self.get_or_create_user_wallet(user_id)
        suspense = await self.get_system_account(
            AccountType.MPESA_SUSPENSE,
            "mpesa_suspense",
            "M-Pesa Suspense",
        )

        await self._lock_account(wallet.id)
        await self._lock_account(suspense.id)

        ref = f"DEP-{external_reference}"
        return await self.post_entry(
            reference=ref,
            description=description,
            entry_type="deposit",
            lines=[
                (suspense.id, "debit", amount_cents, "External inflow"),
                (wallet.id, "credit", amount_cents, "Deposit credit"),
            ],
            idempotency_key=idempotency_key or external_reference,
            related_user_id=user_id,
            metadata={"external_reference": external_reference},
        )

    async def get_balance_cents(self, user_id: uuid.UUID) -> int:
        wallet = await self.get_or_create_user_wallet(user_id)
        return wallet.balance_cents
