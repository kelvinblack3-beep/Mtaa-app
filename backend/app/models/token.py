"""Solana devnet tokens, holdings, and simulated trades."""
import uuid
from datetime import datetime, timezone
from typing import Optional
import enum

from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, BigInteger, Boolean, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Token(Base):
    __tablename__ = "tokens"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    mint_address: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    decimals: Mapped[int] = mapped_column(Integer, default=9, nullable=False)
    total_supply: Mapped[int] = mapped_column(BigInteger, nullable=False)
    creator_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    # Bonding curve parameters (simulated)
    virtual_sol_reserves: Mapped[int] = mapped_column(BigInteger, default=30_000_000_000, nullable=False)  # lamports
    virtual_token_reserves: Mapped[int] = mapped_column(BigInteger, default=1_073_000_000_000_000, nullable=False)
    real_token_reserves: Mapped[int] = mapped_column(BigInteger, nullable=False)
    real_sol_reserves: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    # Status
    is_verified_onchain: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    network: Mapped[str] = mapped_column(String(16), default="devnet", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TokenHolding(Base):
    """User's simulated + tracked holdings of a token."""
    __tablename__ = "token_holdings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tokens.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)  # raw units
    avg_cost_lamports: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class TradeOrder(Base):
    """Simulated buy/sell order against the bonding curve."""
    __tablename__ = "trade_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tokens.id"), nullable=False, index=True
    )
    side: Mapped[str] = mapped_column(String(4), nullable=False)  # buy | sell
    token_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sol_amount_lamports: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price_per_token: Mapped[float] = mapped_column(Float, nullable=False)
    slippage_bps: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="filled", nullable=False)
    is_simulated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
