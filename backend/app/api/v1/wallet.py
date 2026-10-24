from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.user import User
from app.models.ledger import JournalEntry, JournalLine, Account
from app.schemas.wallet import (
    BalanceOut,
    TransferRequest,
    TransferOut,
    DepositRequest,
    DepositOut,
    HistoryItem,
)
from app.services.ledger import LedgerService, LedgerError, InsufficientFundsError, DuplicateIdempotencyError
from app.services.payments import PaymentService, PaymentError

router = APIRouter(prefix="/wallet", tags=["wallet"])


def cents_to_kes(cents: int) -> str:
    return f"{cents / 100:.2f}"


@router.get("/balance", response_model=BalanceOut)
async def get_balance(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    ledger = LedgerService(db)
    balance = await ledger.get_balance_cents(user.id)
    return BalanceOut(
        balance_cents=balance,
        balance_kes=cents_to_kes(balance),
        currency="KES",
    )


@router.post("/transfer", response_model=TransferOut)
async def transfer(
    body: TransferRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    amount_cents = int(round(body.amount_kes * 100))
    if amount_cents <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Resolve recipient by username or phone
    recipient_q = select(User).where(
        (User.username == body.recipient.lower()) | (User.phone == body.recipient)
    )
    recipient = (await db.execute(recipient_q)).scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")
    if recipient.id == user.id:
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    ledger = LedgerService(db)
    try:
        entry = await ledger.transfer(
            from_user_id=user.id,
            to_user_id=recipient.id,
            amount_cents=amount_cents,
            description=body.description or f"Transfer to @{recipient.username}",
            idempotency_key=body.idempotency_key,
            created_by=user.id,
        )
        return TransferOut(
            reference=entry.reference,
            amount_cents=amount_cents,
            amount_kes=cents_to_kes(amount_cents),
            recipient=recipient.username,
            description=entry.description,
            posted_at=entry.posted_at.isoformat(),
        )
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DuplicateIdempotencyError as e:
        # Return the existing transfer
        entry = e.existing_entry
        return TransferOut(
            reference=entry.reference,
            amount_cents=amount_cents,
            amount_kes=cents_to_kes(amount_cents),
            recipient=recipient.username,
            description=entry.description,
            posted_at=entry.posted_at.isoformat(),
        )
    except LedgerError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deposit", response_model=DepositOut)
async def deposit(
    body: DepositRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    amount_cents = int(round(body.amount_kes * 100))
    svc = PaymentService(db)
    try:
        intent = await svc.initiate_deposit(
            user_id=user.id,
            amount_cents=amount_cents,
            phone=body.phone or user.phone,
            idempotency_key=body.idempotency_key,
        )
        return DepositOut(
            id=str(intent.id),
            external_reference=intent.external_reference,
            amount_cents=intent.amount_cents,
            amount_kes=cents_to_kes(intent.amount_cents),
            status=intent.status,
            provider=intent.provider,
            created_at=intent.created_at.isoformat(),
        )
    except PaymentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=list[HistoryItem])
async def history(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
):
    ledger = LedgerService(db)
    wallet = await ledger.get_or_create_user_wallet(user.id)

    q = (
        select(JournalLine)
        .where(JournalLine.account_id == wallet.id)
        .options(selectinload(JournalLine.entry))
        .order_by(JournalLine.id.desc())
        .limit(min(limit, 100))
    )
    lines = (await db.execute(q)).scalars().all()
    items = []
    for line in lines:
        entry = line.entry
        items.append(
            HistoryItem(
                reference=entry.reference,
                entry_type=entry.entry_type,
                description=entry.description,
                amount_cents=line.amount_cents,
                amount_kes=cents_to_kes(line.amount_cents),
                side=line.side,
                posted_at=entry.posted_at.isoformat(),
            )
        )
    return items
