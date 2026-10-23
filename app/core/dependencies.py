"""
FastAPI dependency injection — database session and authentication dependencies.

Auth flow:
  1. Client sends Bearer token in Authorization header.
  2. get_current_user() decodes the JWT, validates claims, loads user from DB.
  3. get_current_active_user() additionally checks is_active flag.
  4. Role/permission checks are handled by app.core.permissions.
"""

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token, is_token_blacklisted
from app.db.session import AsyncSessionLocal

# Points Swagger UI to the correct login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ─── Database Session ─────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield one async DB session per request, with auto commit/rollback."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ─── Current User ─────────────────────────────────────────────────────
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Decode the JWT access token and return the corresponding User.

    Raises 401 for:
      - missing / malformed token
      - expired token
      - token type != "access"
      - user not found in DB

    Raises 403 for:
      - inactive user account
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token tidak valid atau sudah kadaluarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exc

    # Ensure this is an access token, not a refresh token
    if payload.get("type") != "access":
        raise credentials_exc

    # Check JTI blacklist (covers logged-out tokens)
    jti: str | None = payload.get("jti")
    if jti and is_token_blacklisted(jti):
        raise credentials_exc

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exc

    # Lazy import to avoid circular dependency
    from app.repositories.user_repository import UserRepository
    user = await UserRepository(db).get_by_id(int(user_id))

    if user is None:
        raise credentials_exc

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun tidak aktif. Hubungi administrator.",
        )

    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """Alias for get_current_user — use this in route handlers."""
    return current_user
