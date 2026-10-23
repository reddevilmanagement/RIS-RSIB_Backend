"""
Auth service — business logic for login, logout, token refresh, and password change.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    blacklist_token,
    is_token_blacklisted,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshTokenResponse,
    LogoutResponse,
    ChangePasswordRequest,
    UserInToken,
)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    # ─── Login ────────────────────────────────────────────────────────
    async def login(self, credentials: LoginRequest) -> LoginResponse:
        """
        Authenticate user credentials and issue JWT token pair.

        Returns LoginResponse with access token, refresh token, and user info.
        Uses a generic error message to prevent username enumeration.
        """
        user = await self.user_repo.get_by_username(credentials.username)

        # Constant-time comparison — always call verify_password even if user
        # is None to prevent timing-based username enumeration.
        password_ok = verify_password(
            credentials.password,
            user.hashed_password if user else "$2b$12$invalidhashpadding000000000000000000000000000000000000000",
        )

        if not user or not password_ok:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Username atau password salah",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akun tidak aktif. Hubungi administrator.",
            )

        access_token = create_access_token(subject=user.id, role=user.role.value)
        refresh_token, _ = create_refresh_token(subject=user.id)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserInToken(
                id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=user.role.value,
                is_active=user.is_active,
            ),
        )

    # ─── Refresh ──────────────────────────────────────────────────────
    async def refresh_access_token(self, refresh_token: str) -> RefreshTokenResponse:
        """
        Issue a new access token using a valid refresh token.

        The refresh token is validated but NOT rotated here — rotation
        can be added by blacklisting the old JTI and issuing a new refresh token.
        """
        invalid_exc = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token tidak valid atau sudah kadaluarsa",
            headers={"WWW-Authenticate": "Bearer"},
        )

        payload = decode_token(refresh_token)
        if payload is None:
            raise invalid_exc

        if payload.get("type") != "refresh":
            raise invalid_exc

        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            raise invalid_exc

        user_id = payload.get("sub")
        if not user_id:
            raise invalid_exc

        user = await self.user_repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise invalid_exc

        new_access_token = create_access_token(subject=user.id, role=user.role.value)

        return RefreshTokenResponse(
            access_token=new_access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ─── Logout ───────────────────────────────────────────────────────
    async def logout(self, refresh_token: str) -> LogoutResponse:
        """
        Revoke the refresh token by blacklisting its JTI.

        The access token will expire naturally (short TTL).
        For immediate access token revocation, add its JTI to the blacklist too.
        """
        payload = decode_token(refresh_token)
        if payload and payload.get("jti"):
            blacklist_token(payload["jti"])

        return LogoutResponse(message="Logout berhasil. Silakan hapus token dari client.")

    # ─── Change Password ──────────────────────────────────────────────
    async def change_password(
        self,
        user: User,
        data: ChangePasswordRequest,
    ) -> dict:
        """
        Change the authenticated user's password.

        Validates the current password before applying the change.
        """
        if not verify_password(data.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password saat ini tidak sesuai",
            )

        if data.current_password == data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password baru tidak boleh sama dengan password lama",
            )

        await self.user_repo.update(
            user, {"hashed_password": hash_password(data.new_password)}
        )

        return {"message": "Password berhasil diubah"}
