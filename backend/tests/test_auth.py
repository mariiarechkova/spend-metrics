import pytest

from app.core.security import create_refresh_token


@pytest.mark.asyncio
async def test_register_returns_tokens(client):
    response = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client):
    payload = {"email": "test@example.com", "password": "secret123"}
    await client.post("/auth/register", json=payload)

    response = await client.post("/auth/register", json=payload)

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_with_valid_credentials_returns_tokens(client):
    payload = {"email": "test@example.com", "password": "secret123"}
    await client.post("/auth/register", json=payload)

    response = await client.post("/auth/login", json=payload)

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client):
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )

    response = await client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_valid_token_returns_new_tokens(client):
    reg = await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "secret123"},
    )
    me = await client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {reg.json()['access_token']}"},
    )
    user_id = me.json()["id"]

    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": create_refresh_token(user_id)},
    )

    assert response.status_code == 200
    assert response.json()["access_token"]
    assert response.json()["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(client):
    response = await client.post(
        "/auth/refresh",
        json={"refresh_token": "not-a-token"},
    )

    assert response.status_code == 401
