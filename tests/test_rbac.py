"""
Tests for Role-Based Access Control (RBAC).

Verifies that each role can only access what the permission matrix allows.
"""

import pytest
from httpx import AsyncClient


# ─── Helper ───────────────────────────────────────────────────────────

def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─── /api/v1/users — admin only ───────────────────────────────────────

@pytest.mark.asyncio
async def test_list_users_admin_allowed(client: AsyncClient, admin_token):
    resp = await client.get("/api/v1/users", headers=auth(admin_token))
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("token_fixture", ["radiolog_token", "dokter_token", "resepsionis_token"])
async def test_list_users_non_admin_forbidden(
    client: AsyncClient, request, token_fixture
):
    token = request.getfixturevalue(token_fixture)
    resp = await client.get("/api/v1/users", headers=auth(token))
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_create_user_admin_allowed(client: AsyncClient, admin_token):
    resp = await client.post(
        "/api/v1/users",
        json={
            "username": "newuser_rbac",
            "email": "newuser_rbac@test.com",
            "full_name": "New User RBAC",
            "role": "resepsionis",
            "password": "password123",
        },
        headers=auth(admin_token),
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_user_radiolog_forbidden(client: AsyncClient, radiolog_token):
    resp = await client.post(
        "/api/v1/users",
        json={
            "username": "shouldfail",
            "email": "shouldfail@test.com",
            "full_name": "Should Fail",
            "role": "resepsionis",
            "password": "password123",
        },
        headers=auth(radiolog_token),
    )
    assert resp.status_code == 403


# ─── /api/v1/patients ─────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("token_fixture", [
    "admin_token", "radiolog_token", "dokter_token", "resepsionis_token"
])
async def test_list_patients_all_roles_allowed(
    client: AsyncClient, request, token_fixture
):
    token = request.getfixturevalue(token_fixture)
    resp = await client.get("/api/v1/patients", headers=auth(token))
    assert resp.status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("token_fixture", ["admin_token", "resepsionis_token"])
async def test_create_patient_allowed(client: AsyncClient, request, token_fixture):
    token = request.getfixturevalue(token_fixture)
    resp = await client.post(
        "/api/v1/patients",
        json={
            "full_name": f"Pasien Test {token_fixture}",
            "date_of_birth": "1990-01-15",
            "gender": "L",
        },
        headers=auth(token),
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize("token_fixture", ["radiolog_token", "dokter_token"])
async def test_create_patient_forbidden(client: AsyncClient, request, token_fixture):
    token = request.getfixturevalue(token_fixture)
    resp = await client.post(
        "/api/v1/patients",
        json={
            "full_name": "Should Fail",
            "date_of_birth": "1990-01-15",
            "gender": "L",
        },
        headers=auth(token),
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_patient_admin_only(
    client: AsyncClient, admin_token, resepsionis_token
):
    # Create a patient first
    create_resp = await client.post(
        "/api/v1/patients",
        json={"full_name": "To Delete", "date_of_birth": "1985-06-20", "gender": "P"},
        headers=auth(admin_token),
    )
    patient_id = create_resp.json()["id"]

    # Resepsionis cannot delete
    del_resp = await client.delete(
        f"/api/v1/patients/{patient_id}",
        headers=auth(resepsionis_token),
    )
    assert del_resp.status_code == 403

    # Admin can delete
    del_resp = await client.delete(
        f"/api/v1/patients/{patient_id}",
        headers=auth(admin_token),
    )
    assert del_resp.status_code == 204


# ─── /api/v1/dashboard/stats ──────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("token_fixture", [
    "admin_token", "radiolog_token", "dokter_token", "resepsionis_token"
])
async def test_dashboard_stats_all_roles(
    client: AsyncClient, request, token_fixture
):
    token = request.getfixturevalue(token_fixture)
    resp = await client.get("/api/v1/dashboard/stats", headers=auth(token))
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_dashboard_stats_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/dashboard/stats")
    assert resp.status_code == 401


# ─── Token type enforcement ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_token_cannot_access_protected_routes(
    client: AsyncClient, admin_user
):
    """Refresh tokens must be rejected on protected API routes."""
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": admin_user.username, "password": "password123"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert resp.status_code == 401


# ─── Permission helper unit tests ─────────────────────────────────────

def test_permission_matrix():
    """Verify the permission matrix is correctly defined."""
    from app.core.permissions import ROLE_PERMISSIONS, has_permission
    from app.models.user import User, UserRole

    def make_user(role: UserRole) -> User:
        u = User.__new__(User)
        u.role = role
        return u

    admin = make_user(UserRole.ADMIN)
    radiolog = make_user(UserRole.RADIOLOG)
    dokter = make_user(UserRole.DOKTER)
    resepsionis = make_user(UserRole.RESEPSIONIS)

    # Admin has everything
    assert has_permission(admin, "users:delete")
    assert has_permission(admin, "reports:delete")

    # Radiolog can write reports but not delete users
    assert has_permission(radiolog, "reports:create")
    assert not has_permission(radiolog, "users:read")
    assert not has_permission(radiolog, "patients:create")

    # Dokter can read reports but not write them
    assert has_permission(dokter, "reports:read")
    assert not has_permission(dokter, "reports:create")
    assert not has_permission(dokter, "patients:create")

    # Resepsionis can manage patients but not reports
    assert has_permission(resepsionis, "patients:create")
    assert has_permission(resepsionis, "appointments:delete")
    assert not has_permission(resepsionis, "reports:read")
    assert not has_permission(resepsionis, "users:read")
