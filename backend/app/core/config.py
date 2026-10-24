"""Application configuration with safety gates."""
from functools import lru_cache
from typing import List, Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Mtaa"
    app_env: Literal["development", "staging", "production", "test"] = "development"
    debug: bool = False
    secret_key: str = Field(..., min_length=32)
    session_cookie_name: str = "mtaa_session"
    session_max_age_seconds: int = 86400

    # Database
    database_url: str = "postgresql+asyncpg://mtaa:mtaa_dev_password@localhost:5432/mtaa"
    database_url_sync: str = "postgresql://mtaa:mtaa_dev_password@localhost:5432/mtaa"

    # CORS
    frontend_url: str = "http://localhost:3000"
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Auth
    password_min_length: int = 8
    bcrypt_rounds: int = 12

    # Daraja / M-Pesa
    daraja_mode: Literal["simulation", "sandbox"] = "simulation"
    daraja_consumer_key: str = ""
    daraja_consumer_secret: str = ""
    daraja_shortcode: str = ""
    daraja_passkey: str = ""
    daraja_callback_url: str = "http://localhost:8000/api/v1/payments/mpesa/callback"
    daraja_environment: Literal["sandbox", "production"] = "sandbox"

    # Solana
    solana_network: Literal["devnet", "testnet"] = "devnet"
    solana_rpc_url: str = "https://api.devnet.solana.com"

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60

    # Admin bootstrap
    admin_bootstrap_username: str = ""
    admin_bootstrap_password: str = ""

    @property
    def origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @field_validator("solana_network")
    @classmethod
    def reject_mainnet(cls, v: str) -> str:
        if v and v.lower() in ("mainnet", "mainnet-beta"):
            raise ValueError(
                "SAFETY GATE: Solana mainnet is forbidden. "
                "Mtaa is a testnet-only prototype. Use 'devnet' or 'testnet'."
            )
        return v

    @field_validator("daraja_environment")
    @classmethod
    def reject_live_daraja(cls, v: str) -> str:
        if v and v.lower() == "production":
            raise ValueError(
                "SAFETY GATE: Live M-Pesa / Daraja production is forbidden. "
                "Use 'sandbox' or set DARAJA_MODE=simulation."
            )
        return v

    @model_validator(mode="after")
    def enforce_safety_defaults(self) -> "Settings":
        # Force simulation mode if anything looks production-like
        if self.daraja_environment == "production":
            raise ValueError("Cannot run with daraja_environment=production")
        if self.solana_network not in ("devnet", "testnet"):
            raise ValueError("solana_network must be devnet or testnet")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
