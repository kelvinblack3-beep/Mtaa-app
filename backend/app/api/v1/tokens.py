from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser, OptionalUser
from app.services.tokens import TokenService, TokenError
from app.adapters.solana import SolanaSafetyError

router = APIRouter(prefix="/tokens", tags=["tokens"])


class CreateTokenRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    symbol: str = Field(..., min_length=1, max_length=10)
    description: Optional[str] = None
    image_url: Optional[str] = None


class QuoteRequest(BaseModel):
    sol_lamports: Optional[int] = Field(None, gt=0)
    token_amount: Optional[int] = Field(None, gt=0)
    side: str = Field(..., pattern="^(buy|sell)$")


class TradeRequest(BaseModel):
    sol_lamports: Optional[int] = Field(None, gt=0)
    token_amount: Optional[int] = Field(None, gt=0)
    side: str = Field(..., pattern="^(buy|sell)$")
    slippage_bps: int = Field(100, ge=0, le=5000)


def token_out(t) -> dict:
    from app.services.bonding_curve import BondingCurve
    curve = BondingCurve(t.virtual_sol_reserves, t.virtual_token_reserves)
    return {
        "id": str(t.id),
        "mint_address": t.mint_address,
        "name": t.name,
        "symbol": t.symbol,
        "description": t.description,
        "image_url": t.image_url,
        "decimals": t.decimals,
        "total_supply": t.total_supply,
        "creator_id": str(t.creator_id),
        "spot_price_sol": curve.spot_price,
        "virtual_sol_reserves": t.virtual_sol_reserves,
        "virtual_token_reserves": t.virtual_token_reserves,
        "is_verified_onchain": t.is_verified_onchain,
        "network": t.network,
        "status": t.status,
        "created_at": t.created_at.isoformat(),
        "label": "SIMULATED / DEVNET ONLY",
    }


@router.get("")
async def list_tokens(db: AsyncSession = Depends(get_db), limit: int = 50):
    svc = TokenService(db)
    tokens = await svc.list_tokens(limit=limit)
    return [token_out(t) for t in tokens]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_token(
    body: CreateTokenRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    svc = TokenService(db)
    try:
        token = await svc.create_token(
            creator_id=user.id,
            name=body.name,
            symbol=body.symbol,
            description=body.description,
            image_url=body.image_url,
        )
        return token_out(token)
    except (TokenError, SolanaSafetyError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/mint/{mint}")
async def get_by_mint(mint: str, db: AsyncSession = Depends(get_db)):
    svc = TokenService(db)
    token = await svc.get_by_mint(mint)
    if not token:
        raise HTTPException(status_code=404, detail="Token not found")
    return token_out(token)


@router.post("/{token_id}/quote")
async def quote(
    token_id: str,
    body: QuoteRequest,
    db: AsyncSession = Depends(get_db),
):
    import uuid
    svc = TokenService(db)
    try:
        tid = uuid.UUID(token_id)
        if body.side == "buy":
            if not body.sol_lamports:
                raise HTTPException(400, "sol_lamports required for buy")
            return await svc.quote_buy(tid, body.sol_lamports)
        else:
            if not body.token_amount:
                raise HTTPException(400, "token_amount required for sell")
            return await svc.quote_sell(tid, body.token_amount)
    except TokenError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{token_id}/trade")
async def trade(
    token_id: str,
    body: TradeRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    import uuid
    svc = TokenService(db)
    try:
        tid = uuid.UUID(token_id)
        if body.side == "buy":
            if not body.sol_lamports:
                raise HTTPException(400, "sol_lamports required for buy")
            order = await svc.execute_buy(
                user_id=user.id,
                token_id=tid,
                sol_lamports=body.sol_lamports,
                slippage_bps=body.slippage_bps,
            )
        else:
            if not body.token_amount:
                raise HTTPException(400, "token_amount required for sell")
            order = await svc.execute_sell(
                user_id=user.id,
                token_id=tid,
                token_amount=body.token_amount,
                slippage_bps=body.slippage_bps,
            )
        return {
            "id": str(order.id),
            "side": order.side,
            "token_amount": order.token_amount,
            "sol_amount_lamports": order.sol_amount_lamports,
            "price_per_token": order.price_per_token,
            "is_simulated": order.is_simulated,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "label": "SIMULATED TRADE — NOT ON-CHAIN",
        }
    except TokenError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/portfolio/me")
async def my_portfolio(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    svc = TokenService(db)
    return await svc.portfolio(user.id)
