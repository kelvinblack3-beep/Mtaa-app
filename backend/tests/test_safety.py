"""Configuration safety gate tests."""
import pytest
from pydantic import ValidationError


def test_mainnet_rejected():
    from app.core.config import Settings
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            secret_key="x" * 32,
            solana_network="mainnet",
        )


def test_mainnet_beta_rejected():
    from app.core.config import Settings
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            secret_key="x" * 32,
            solana_network="mainnet-beta",
        )


def test_live_daraja_rejected():
    from app.core.config import Settings
    with pytest.raises((ValidationError, ValueError)):
        Settings(
            secret_key="x" * 32,
            daraja_environment="production",
        )


def test_devnet_accepted():
    from app.core.config import Settings
    s = Settings(
        secret_key="x" * 32,
        solana_network="devnet",
        daraja_mode="simulation",
        daraja_environment="sandbox",
    )
    assert s.solana_network == "devnet"
