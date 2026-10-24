"""Token creation, holdings, and simulated trading."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.solana import SolanaAdapter, SolanaSafetyError
from app.models.token import Token, TokenHolding, TradeOrder
from app.services.bonding_curve import BondingCurve

# Default virtual reserves (inspired by pump.fun style curves)
DEFAULT_VIRTUAL_SOL = 30_000_000_000          # 30 SOL in lamports
DEFAULT_VIRTUAL_TOKEN = 1_073_000_000_000_000  # ~1.073B tokens (9 decimals)
DEFAULT_SUPPLY = 1_000_000_000_000_000         # 1B tokens raw


class TokenError(Exception):
    pass


class TokenService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.solana = SolanaAdapter()

    async def create_token(
        self,
        *,
        creator_id: uuid.UUID,
        name: str,
        symbol: str,
        description: Optional[str] = None,
        image_url: Optional[str] = None,
        decimals: int = 9,
        total_supply: int = DEFAULT_SUPPLY,
    ) -> Token:
        self.solana.assert_devnet_only()
        symbol = symbol.upper().strip()
        if not (1 <= len(symbol) <= 10):
            raise TokenError("Symbol must be 1-10 characters")
        if not (1 <= len(name) <= 100):
            raise TokenError("Name must be 1-100 characters")

        mint = self.solana.generate_mint_address(seed=f"{creator_id}:{symbol}:{name}")

        token = Token(
            mint_address=mint,
            name=name,
            symbol=symbol,
            description=description,
            image_url=image_url,
            decimals=decimals,
            total_supply=total_supply,
            creator_id=creator_id,
            virtual_sol_reserves=DEFAULT_VIRTUAL_SOL,
            virtual_token_reserves=DEFAULT_VIRTUAL_TOKEN,
            real_token_reserves=total_supply,
            real_sol_reserves=0,
            is_verified_onchain=False,  # not claimed until independently verified
            network=self.solana.network,
            status="active",
        )
        self.db.add(token)
        await self.db.flush()
        return token

    def _curve(self, token: Token) -> BondingCurve:
        return BondingCurve(token.virtual_sol_reserves, token.virtual_token_reserves)

    async def quote_buy(self, token_id: uuid.UUID, sol_lamports: int) -> dict:
        token = await self._get_token(token_id)
        curve = self._curve(token)
        q = curve.quote_buy(sol_lamports)
        return {
            "side": "buy",
            "token_amount": q.token_amount,
            "sol_lamports": q.sol_amount_lamports,
            "price_per_token": q.price_per_token,
            "price_impact_bps": q.price_impact_bps,
            "is_simulated": True,
        }

    async def quote_sell(self, token_id: uuid.UUID, token_amount: int) -> dict:
        token = await self._get_token(token_id)
        curve = self._curve(token)
        q = curve.quote_sell(token_amount)
        return {
            "side": "sell",
            "token_amount": q.token_amount,
            "sol_lamports": q.sol_amount_lamports,
            "price_per_token": q.price_per_token,
            "price_impact_bps": q.price_impact_bps,
            "is_simulated": True,
        }

    async def execute_buy(
        self,
        *,
        user_id: uuid.UUID,
        token_id: uuid.UUID,
        sol_lamports: int,
        slippage_bps: int = 100,
    ) -> TradeOrder:
        token = await self._get_token(token_id)
        curve = self._curve(token)
        q = curve.quote_buy(sol_lamports)

        # Apply trade to curve reserves
        token.virtual_sol_reserves = q.new_virtual_sol
        token.virtual_token_reserves = q.new_virtual_token
        token.real_sol_reserves += sol_lamports
        token.real_token_reserves -= q.token_amount

        # Update holdings
        holding = await self._get_or_create_holding(user_id, token_id)
        holding.amount += q.token_amount
        holding.updated_at = datetime.now(timezone.utc)

        order = TradeOrder(
            user_id=user_id,
            token_id=token_id,
            side="buy",
            token_amount=q.token_amount,
            sol_amount_lamports=sol_lamports,
            price_per_token=q.price_per_token,
            slippage_bps=slippage_bps,
            status="filled",
            is_simulated=True,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    async def execute_sell(
        self,
        *,
        user_id: uuid.UUID,
        token_id: uuid.UUID,
        token_amount: int,
        slippage_bps: int = 100,
    ) -> TradeOrder:
        token = await self._get_token(token_id)
        holding = await self._get_or_create_holding(user_id, token_id)
        if holding.amount < token_amount:
            raise TokenError("Insufficient token balance")

        curve = self._curve(token)
        q = curve.quote_sell(token_amount)

        token.virtual_sol_reserves = q.new_virtual_sol
        token.virtual_token_reserves = q.new_virtual_token
        token.real_sol_reserves = max(0, token.real_sol_reserves - q.sol_amount_lamports)
        token.real_token_reserves += token_amount

        holding.amount -= token_amount
        holding.updated_at = datetime.now(timezone.utc)

        order = TradeOrder(
            user_id=user_id,
            token_id=token_id,
            side="sell",
            token_amount=token_amount,
            sol_amount_lamports=q.sol_amount_lamports,
            price_per_token=q.price_per_token,
            slippage_bps=slippage_bps,
            status="filled",
            is_simulated=True,
        )
        self.db.add(order)
        await self.db.flush()
        return order

    async def list_tokens(self, limit: int = 50) -> List[Token]:
        q = select(Token).where(Token.status == "active").order_by(Token.created_at.desc()).limit(limit)
        return list((await self.db.execute(q)).scalars().all())

    async def get_by_mint(self, mint: str) -> Optional[Token]:
        q = select(Token).where(Token.mint_address == mint)
        return (await self.db.execute(q)).scalar_one_or_none()

    async def portfolio(self, user_id: uuid.UUID) -> List[dict]:
        q = select(TokenHolding).where(TokenHolding.user_id == user_id).where(TokenHolding.amount > 0)
        holdings = (await self.db.execute(q)).scalars().all()
        result = []
        for h in holdings:
            token = await self._get_token(h.token_id)
            curve = self._curve(token)
            value_lamports = int(h.amount * curve.spot_price * 1e9 / (10 ** token.decimals))
            result.append({
                "token_id": str(token.id),
                "mint": token.mint_address,
                "symbol": token.symbol,
                "name": token.name,
                "amount": h.amount,
                "decimals": token.decimals,
                "spot_price_sol": curve.spot_price,
                "estimated_value_lamports": value_lamports,
                "is_simulated": True,
                "network": token.network,
            })
        return result

    async def _get_token(self, token_id: uuid.UUID) -> Token:
        q = select(Token).where(Token.id == token_id)
        token = (await self.db.execute(q)).scalar_one_or_none()
        if not token:
            raise TokenError("Token not found")
        return token

    async def _get_or_create_holding(self, user_id: uuid.UUID, token_id: uuid.UUID) -> TokenHolding:
        q = select(TokenHolding).where(
            TokenHolding.user_id == user_id, TokenHolding.token_id == token_id
        )
        h = (await self.db.execute(q)).scalar_one_or_none()
        if h:
            return h
        h = TokenHolding(user_id=user_id, token_id=token_id, amount=0, avg_cost_lamports=0)
        self.db.add(h)
        await self.db.flush()
        return h
