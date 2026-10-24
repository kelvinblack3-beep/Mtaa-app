"""Solana devnet adapter.

Restricted to devnet/testnet. Mainnet is rejected by configuration.
Token creation uses SPL Token concepts; actual on-chain minting requires
external wallet signing in production. This adapter records mint addresses
and verifies network.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


class SolanaSafetyError(Exception):
    pass


class SolanaAdapter:
    def __init__(self):
        if settings.solana_network not in ("devnet", "testnet"):
            raise SolanaSafetyError(
                f"Forbidden network: {settings.solana_network}. Only devnet/testnet allowed."
            )
        self.network = settings.solana_network
        self.rpc_url = settings.solana_rpc_url

    def generate_mint_address(self, seed: Optional[str] = None) -> str:
        """Generate a deterministic-looking base58-like mint address for simulation.

        In a full integration this would come from an actual create-mint transaction.
        We clearly mark tokens as not verified until independently checked.
        """
        raw = (seed or uuid.uuid4().hex).encode() + self.network.encode()
        digest = hashlib.sha256(raw).hexdigest()
        # Produce a 44-char base58-ish string (not real base58, but distinctive)
        return f"MT{digest[:42]}"

    def validate_public_key(self, address: str) -> bool:
        if not address or len(address) < 32 or len(address) > 64:
            return False
        return True

    def network_label(self) -> str:
        return f"Solana {self.network.upper()}"

    def assert_devnet_only(self) -> None:
        if self.network == "mainnet" or "mainnet" in self.rpc_url.lower():
            raise SolanaSafetyError("Mainnet is forbidden")
