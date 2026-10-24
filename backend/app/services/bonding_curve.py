"""Simulated constant-product bonding curve (x * y = k).

All calculations are deterministic and clearly labelled as simulated.
Price impact and slippage are computed from virtual reserves.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Quote:
    token_amount: int
    sol_amount_lamports: int
    price_per_token: float
    price_impact_bps: int
    new_virtual_sol: int
    new_virtual_token: int


class BondingCurve:
    """Constant-product AMM simulator."""

    def __init__(self, virtual_sol: int, virtual_token: int):
        if virtual_sol <= 0 or virtual_token <= 0:
            raise ValueError("Reserves must be positive")
        self.virtual_sol = virtual_sol
        self.virtual_token = virtual_token

    @property
    def k(self) -> int:
        return self.virtual_sol * self.virtual_token

    @property
    def spot_price(self) -> float:
        """SOL per token (in SOL, not lamports)."""
        return (self.virtual_sol / 1e9) / (self.virtual_token / 1e9)

    def quote_buy(self, sol_lamports: int) -> Quote:
        """Buy tokens with SOL."""
        if sol_lamports <= 0:
            raise ValueError("SOL amount must be positive")
        new_sol = self.virtual_sol + sol_lamports
        new_token = self.k // new_sol
        tokens_out = self.virtual_token - new_token
        if tokens_out <= 0:
            raise ValueError("Insufficient liquidity")
        price = (sol_lamports / 1e9) / (tokens_out / 1e9)
        spot = self.spot_price
        impact_bps = int(round(abs(price - spot) / spot * 10000)) if spot > 0 else 0
        return Quote(
            token_amount=tokens_out,
            sol_amount_lamports=sol_lamports,
            price_per_token=price,
            price_impact_bps=impact_bps,
            new_virtual_sol=new_sol,
            new_virtual_token=new_token,
        )

    def quote_sell(self, token_amount: int) -> Quote:
        """Sell tokens for SOL."""
        if token_amount <= 0:
            raise ValueError("Token amount must be positive")
        if token_amount >= self.virtual_token:
            raise ValueError("Cannot sell more than virtual reserves")
        new_token = self.virtual_token + token_amount
        new_sol = self.k // new_token
        sol_out = self.virtual_sol - new_sol
        if sol_out <= 0:
            raise ValueError("Insufficient liquidity")
        price = (sol_out / 1e9) / (token_amount / 1e9)
        spot = self.spot_price
        impact_bps = int(round(abs(price - spot) / spot * 10000)) if spot > 0 else 0
        return Quote(
            token_amount=token_amount,
            sol_amount_lamports=sol_out,
            price_per_token=price,
            price_impact_bps=impact_bps,
            new_virtual_sol=new_sol,
            new_virtual_token=new_token,
        )

    def apply(self, quote: Quote) -> None:
        self.virtual_sol = quote.new_virtual_sol
        self.virtual_token = quote.new_virtual_token
