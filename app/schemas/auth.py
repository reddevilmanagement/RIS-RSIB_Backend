"""
Pydantic schemas for authentication endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# ─── Request schemas ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

    class Config:
        # Prevent accidental logging of passwords
        json_schema_extra = {
            "example": {
                "current_password": "••••••••",
                "new_password": "••••••••",
            }
        }


# ─── Response schemas ─────────────────────────────────────────────────

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires


class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutResponse(BaseModel):
    message: str


# ─── Internal / payload schemas ───────────────────────────────────────

class TokenPayload(BaseModel):
    sub: str           # user ID
    role: str          # UserRole value
    jti: str           # unique token ID
    type: str          # "access" | "refresh"
    iat: Optional[datetime] = None
    exp: Optional[datetime] = None


class UserInToken(BaseModel):
    """Minimal user info embedded in the token response."""
    id: int
    username: str
    full_name: str
    role: str
    is_active: bool


class LoginResponse(BaseModel):
    """Extended login response that includes user info alongside tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInToken
