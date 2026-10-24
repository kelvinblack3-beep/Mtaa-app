"""Double-entry ledger invariant tests."""
import uuid
import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.user import User
from app.services.ledger import (
    LedgerService,
    InsufficientFundsError,
    UnbalancedEntryError,
    DuplicateIdempotencyError,
)
from app.core.security import hash_password


@pytest_asyncio.fixture
async def two_users(db):
    u1 = User(
        username="alice",
        email="alice@test.com",
        hashed_password=hash_password("password123"),
        role="user",
    )
    u2 = User(
        username="bob",
        email="bob@test.com",
        hashed_password=hash_password("password123"),
        role="user",
    )
    db.add_all([u1, u2])
    await db.flush()
    return u1, u2


@pytest.mark.asyncio
async def test_deposit_and_balance(db, two_users):
    alice, _ = two_users
    ledger = LedgerService(db)
    await ledger.credit_deposit(
        user_id=alice.id,
        amount_cents=10_000_00,  # 10,000 KES
        external_reference="TESTDEP001",
    )
    bal = await ledger.get_balance_cents(alice.id)
    assert bal == 10_000_00


@pytest.mark.asyncio
async def test_transfer_success(db, two_users):
    alice, bob = two_users
    ledger = LedgerService(db)
    await ledger.credit_deposit(
        user_id=alice.id, amount_cents=5_000_00, external_reference="DEP002"
    )
    entry = await ledger.transfer(
        from_user_id=alice.id,
        to_user_id=bob.id,
        amount_cents=1_500_00,
        description="Test transfer",
    )
    assert entry.reference.startswith("TRF-")
    assert await ledger.get_balance_cents(alice.id) == 3_500_00
    assert await ledger.get_balance_cents(bob.id) == 1_500_00


@pytest.mark.asyncio
async def test_insufficient_funds(db, two_users):
    alice, bob = two_users
    ledger = LedgerService(db)
    await ledger.credit_deposit(
        user_id=alice.id, amount_cents=100_00, external_reference="DEP003"
    )
    with pytest.raises(InsufficientFundsError):
        await ledger.transfer(
            from_user_id=alice.id,
            to_user_id=bob.id,
            amount_cents=500_00,
        )


@pytest.mark.asyncio
async def test_duplicate_idempotency(db, two_users):
    alice, bob = two_users
    ledger = LedgerService(db)
    await ledger.credit_deposit(
        user_id=alice.id, amount_cents=10_000_00, external_reference="DEP004"
    )
    key = "idem-unique-001"
    e1 = await ledger.transfer(
        from_user_id=alice.id,
        to_user_id=bob.id,
        amount_cents=100_00,
        idempotency_key=key,
    )
    with pytest.raises(DuplicateIdempotencyError) as exc:
        await ledger.transfer(
            from_user_id=alice.id,
            to_user_id=bob.id,
            amount_cents=100_00,
            idempotency_key=key,
        )
    assert exc.value.existing_entry.id == e1.id
    # Balance only debited once
    assert await ledger.get_balance_cents(alice.id) == 9_900_00


@pytest.mark.asyncio
async def test_balanced_entry_enforced(db, two_users):
    alice, _ = two_users
    ledger = LedgerService(db)
    wallet = await ledger.get_or_create_user_wallet(alice.id)
    with pytest.raises(UnbalancedEntryError):
        await ledger.post_entry(
            reference="BAD-001",
            description="Unbalanced",
            entry_type="adjustment",
            lines=[
                (wallet.id, "credit", 1000, None),
                # missing balancing debit
            ],
        )
