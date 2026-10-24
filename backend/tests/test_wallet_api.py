"""Wallet API integration tests."""
import pytest


async def _register_login(client, username="walletuser", email="wallet@test.com"):
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": "securepass99",
        },
    )
    r = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": username, "password": "securepass99"},
    )
    assert r.status_code == 200
    return r


@pytest.mark.asyncio
async def test_deposit_and_balance(client):
    await _register_login(client)
    r = await client.post(
        "/api/v1/wallet/deposit",
        json={"amount_kes": 2500.50},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["status"] == "completed"
    assert data["amount_cents"] == 250050

    bal = await client.get("/api/v1/wallet/balance")
    assert bal.status_code == 200
    assert bal.json()["balance_cents"] == 250050


@pytest.mark.asyncio
async def test_transfer_between_users(client):
    await _register_login(client, "sender", "sender@test.com")
    await client.post("/api/v1/wallet/deposit", json={"amount_kes": 1000})

    # Register recipient
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "receiver",
            "email": "receiver@test.com",
            "password": "securepass99",
        },
    )

    r = await client.post(
        "/api/v1/wallet/transfer",
        json={"recipient": "receiver", "amount_kes": 300},
    )
    assert r.status_code == 200, r.text
    assert r.json()["amount_cents"] == 30000

    bal = await client.get("/api/v1/wallet/balance")
    assert bal.json()["balance_cents"] == 70000


@pytest.mark.asyncio
async def test_transfer_insufficient(client):
    await _register_login(client, "poor", "poor@test.com")
    await client.post(
        "/api/v1/auth/register",
        json={
            "username": "richguy",
            "email": "rich@test.com",
            "password": "securepass99",
        },
    )
    r = await client.post(
        "/api/v1/wallet/transfer",
        json={"recipient": "richguy", "amount_kes": 50},
    )
    assert r.status_code == 400
