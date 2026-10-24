"""Bonding curve quote and slippage tests."""
import pytest
from app.services.bonding_curve import BondingCurve


def test_spot_price():
    curve = BondingCurve(30_000_000_000, 1_073_000_000_000_000)
    assert curve.spot_price > 0


def test_buy_quote_positive():
    curve = BondingCurve(30_000_000_000, 1_073_000_000_000_000)
    q = curve.quote_buy(1_000_000_000)  # 1 SOL
    assert q.token_amount > 0
    assert q.sol_amount_lamports == 1_000_000_000
    assert q.price_per_token > 0
    assert q.new_virtual_sol > curve.virtual_sol
    assert q.new_virtual_token < curve.virtual_token


def test_sell_quote_positive():
    curve = BondingCurve(30_000_000_000, 1_073_000_000_000_000)
    # First buy some
    buy = curve.quote_buy(1_000_000_000)
    curve.apply(buy)
    sell = curve.quote_sell(buy.token_amount // 2)
    assert sell.sol_amount_lamports > 0
    assert sell.token_amount == buy.token_amount // 2


def test_buy_increases_price():
    curve = BondingCurve(30_000_000_000, 1_073_000_000_000_000)
    spot_before = curve.spot_price
    q = curve.quote_buy(5_000_000_000)
    curve.apply(q)
    assert curve.spot_price > spot_before


def test_zero_amount_raises():
    curve = BondingCurve(30_000_000_000, 1_073_000_000_000_000)
    with pytest.raises(ValueError):
        curve.quote_buy(0)
    with pytest.raises(ValueError):
        curve.quote_sell(0)


def test_price_impact_non_negative():
    curve = BondingCurve(30_000_000_000, 1_073_000_000_000_000)
    q = curve.quote_buy(10_000_000_000)
    assert q.price_impact_bps >= 0
