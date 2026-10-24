"""Mtaa FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1 import auth, wallet, health

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: safety banner
    print(f"Starting {settings.app_name} [{settings.app_env}]")
    print(f"  Daraja mode : {settings.daraja_mode}")
    print(f"  Solana net  : {settings.solana_network}")
    print("  SAFETY: mainnet & live M-Pesa are rejected by configuration guards")
    yield
    print("Shutting down Mtaa API")


app = FastAPI(
    title=settings.app_name,
    description=(
        "Mtaa — Kenyan fintech & crypto-community platform (testnet / simulation only). "
        "No real-money custody. Solana devnet + M-Pesa sandbox/simulation only."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(wallet.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "name": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
        "notice": "Testnet / simulation only. No real money.",
    }
