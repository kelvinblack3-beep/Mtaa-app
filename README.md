# Mtaa

**Mtaa** is a mobile-first Kenyan fintech and crypto-community platform (testnet / simulation only).

> **Safety notice**: This is a prototype restricted to Solana **devnet** and M-Pesa **sandbox / local simulation**.  
> It does **not** handle real money, live M-Pesa, Solana mainnet, or real-money custody.

## Features

- KSh-denominated double-entry ledger wallet
- Free internal transfers between registered users
- Safaricom M-Pesa Daraja sandbox adapter + local payment simulator
- Solana devnet SPL token creation & verification
- Token launchpad with simulated bonding-curve trading engine
- Token portfolios, simulated P&L, charts, trading history
- Social feeds, communities, posts, comments, creator profiles, moderation
- Administration, audit logs, role-based access control

## Stack

| Layer        | Technology                                      |
|--------------|-------------------------------------------------|
| Frontend     | Next.js (App Router), TypeScript, Tailwind CSS  |
| Backend      | Python FastAPI, Pydantic, SQLAlchemy 2 (async)  |
| Database     | PostgreSQL + Alembic migrations                 |
| Auth         | Server-managed sessions, bcrypt password hashing|
| Blockchain   | Solana devnet + SPL Token                       |
| Payments     | Daraja sandbox + local simulator                |
| Tests        | Pytest (API + unit), frontend component tests   |

## Repository Structure

```
Mtaa-app/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── api/             # Route modules
│   │   ├── core/            # Config, security, deps
│   │   ├── models/          # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   ├── adapters/        # Daraja, Solana, etc.
│   │   └── main.py
│   ├── alembic/             # Migrations
│   ├── tests/
│   └── requirements.txt
├── frontend/                # Next.js application
│   ├── app/                 # App Router pages
│   ├── components/
│   ├── lib/
│   └── package.json
├── docker-compose.yml
├── render.yaml              # Deployment manifest (for later use)
├── .env.example
└── README.md
```

## Quick Start (Local Development)

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Docker (optional but recommended)

### 1. Clone & configure

```bash
git clone https://github.com/kelvinblack3-beep/Mtaa-app.git
cd Mtaa-app
cp .env.example .env
# Edit .env — set SECRET_KEY and database credentials
```

### 2. Database

```bash
# Using Docker
docker compose up -d db

# Or point DATABASE_URL to your local Postgres
```

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### 5. Run tests

```bash
cd backend
pytest -v --tb=short
```

## Architecture Notes

- **Double-entry ledger**: All KSh movements are posted as balanced journal entries (debits = credits). Amounts stored as integer cents.
- **Idempotency**: Transfers and payment callbacks use unique references / idempotency keys.
- **Safety gates**: Configuration rejects Solana mainnet and live Daraja production settings.
- **Roles**: `user`, `moderator`, `admin`. Authorization is enforced server-side.
- **Sessions**: HTTP-only, secure cookies with rotation and expiration.

## Deployment

`render.yaml` is provided for later deployment by the operator.  
This repository does **not** create or modify any Render services.

## License

Proprietary — all rights reserved.
