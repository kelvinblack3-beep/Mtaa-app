"""Authentication tests."""
import pytest


@pytest.mark.asyncio
async def test_register_and_login(client):
    # Register
    r = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser1",
            "email": "testuser1@example.com",
            "password": "securepass99",
            "display_name": "Test User",
        },
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["username"] == "testuser1"
    assert data["role"] == "user"

    # Login
    r2 = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "testuser1", "password": "securepass99"},
    )
    assert r2.status_code == 200, r2.text
    assert "mtaa_session" in r2.cookies or r2.headers.get("set-cookie")


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    payload = {
        "username": "dupuser",
        "email": "dup1@example.com",
        "password": "securepass99",
    }
    r1 = await client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201
    payload["email"] = "dup2@example.com"
    r2 = await client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid(client):
    r = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "nobody", "password": "wrong"},
    )
    assert r.status_code == 401
