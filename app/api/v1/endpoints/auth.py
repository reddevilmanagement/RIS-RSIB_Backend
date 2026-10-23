"""
Authentication endpoints — login, logout, token refresh, password change.

Public endpoints  : POST /login
Protected endpoints: POST /logout, POST /refresh, POST /change-password, GET /me
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LogoutResponse,
    ChangePasswordRequest,
)
from app.schemas.user import UserMe
from app.services.auth_service import AuthService

router = APIRouter()


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login pengguna",
    description=(
        "Autentikasi dengan username dan password. "
        "Mengembalikan access token (30 menit), refresh token (7 hari), "
        "dan informasi profil pengguna."
    ),
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    credentials = LoginRequest(username=form_data.username, password=form_data.password)
    return await service.login(credentials)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Perbarui access token",
    description="Gunakan refresh token yang valid untuk mendapatkan access token baru.",
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.refresh_access_token(body.refresh_token)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout pengguna",
    description="Mencabut refresh token. Client wajib menghapus kedua token dari storage.",
)
async def logout(
    body: RefreshTokenRequest,
    _: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.logout(body.refresh_token)


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Ganti password",
    description="Ganti password pengguna yang sedang login. Memerlukan password lama.",
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    return await service.change_password(current_user, body)


@router.get(
    "/me",
    response_model=UserMe,
    status_code=status.HTTP_200_OK,
    summary="Profil pengguna saat ini",
    description="Mengembalikan data profil lengkap pengguna yang sedang terautentikasi.",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    return current_user
