from typing import Optional, List
from pydantic import BaseModel, Field


class BalanceOut(BaseModel):
    balance_cents: int
    balance_kes: str
    currency: str = "KES"


class TransferRequest(BaseModel):
    recipient: str = Field(..., description="Username or verified phone of recipient")
    amount_kes: float = Field(..., gt=0, description="Amount in KES (will be converted to cents)")
    description: Optional[str] = Field(None, max_length=255)
    idempotency_key: Optional[str] = Field(None, max_length=128)


class TransferOut(BaseModel):
    reference: str
    amount_cents: int
    amount_kes: str
    recipient: str
    description: str
    posted_at: str


class DepositRequest(BaseModel):
    amount_kes: float = Field(..., gt=0)
    phone: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=128)


class DepositOut(BaseModel):
    id: str
    external_reference: str
    amount_cents: int
    amount_kes: str
    status: str
    provider: str
    created_at: str


class HistoryItem(BaseModel):
    reference: str
    entry_type: str
    description: str
    amount_cents: int
    amount_kes: str
    side: str
    posted_at: str
