"""Double-entry accounting ledger models.

All monetary amounts are stored as integer cents (KES * 100).
Every JournalEntry must have balanced JournalLines (sum debits == sum credits).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
import enum

from sqlalchemy import (
    String, Integer, DateTime, ForeignKey, Text, Boolean, BigInteger,
    CheckConstraint, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class AccountType(str, enum.Enum):
    USER_WALLET = "user_wallet"          # liability to the user
    SYSTEM_CLEARING = "system_clearing"  # internal clearing
    SYSTEM_FEES = "system_fees"          # fee income (zero fees currently)
    MPESA_SUSPENSE = "mpesa_suspense"    # pending external deposits
    EXTERNAL = "external"                # counterpart for external flows


class Account(Base):
    """Chart of accounts entry. User wallets are liability accounts."""
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="KES", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Cached balance in cents — updated atomically with journal posts
    balance_cents: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = relationship("User", back_populates="accounts")
    lines = relationship("JournalLine", back_populates="account")

    __table_args__ = (
        CheckConstraint("balance_cents >= 0", name="ck_account_balance_non_negative"),
    )


class JournalEntry(Base):
    """A balanced set of journal lines. Immutable once posted."""
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    reference: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    entry_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # transfer | deposit | withdrawal | fee | reversal | adjustment
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    related_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    # Soft indicator that a compensating entry exists
    reversed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id"), nullable=True
    )

    lines: Mapped[List["JournalLine"]] = relationship(
        "JournalLine", back_populates="entry", cascade="all, delete-orphan"
    )


class JournalLine(Base):
    """Individual debit or credit line. Amount always positive; side indicates direction."""
    __tablename__ = "journal_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journal_entries.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="RESTRICT"),
        nullable=False, index=True,
    )
    side: Mapped[str] = mapped_column(String(6), nullable=False)  # debit | credit
    amount_cents: Mapped[int] = mapped_column(BigInteger, nullable=False)
    memo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    entry = relationship("JournalEntry", back_populates="lines")
    account = relationship("Account", back_populates="lines")

    __table_args__ = (
        CheckConstraint("amount_cents > 0", name="ck_journal_line_positive_amount"),
        CheckConstraint("side IN ('debit', 'credit')", name="ck_journal_line_side"),
    )
