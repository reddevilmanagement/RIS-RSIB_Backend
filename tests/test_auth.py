"""
Tests for authentication endpoints — login, logout, refresh, change-password.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, admin_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "password123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0
    assert body["user"]["username"] == admin_user.username
    assert body["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, admin_user):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "wrongpassword"},
    )
    assert resp.status_code == 401
    assert "salah" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "ghost_user", "password": "password123"},
    )
    # Must return 401, not 404 (prevent username enumeration)
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, admin_token, admin_user):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == admin_user.username


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this.is.not.valid"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, admin_user):
    # Login to get tokens
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Use refresh token to get new access token
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient, admin_token):
    """Access tokens must not be accepted as refresh tokens."""
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": admin_token},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, admin_user, admin_token):
    # Get refresh token
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Logout
    resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # Refresh token should now be invalid
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password(client: AsyncClient, db_session, admin_user, admin_token):
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "password123", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200

    # Old password should no longer work
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "password123"},
    )
    assert login_resp.status_code == 401


@pytest.mark.asyncio
async def test_change_password_wrong_current(client: AsyncClient, admin_token):
    resp = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongpassword", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400
