"""
Pydantic schemas for User — request/response DTOs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


# ─── Request schemas ──────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole = UserRole.RESEPSIONIS
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v

    @field_validator("username")
    @classmethod
    def username_format(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username hanya boleh mengandung huruf, angka, _ dan -")
        if len(v) < 3:
            raise ValueError("Username minimal 3 karakter")
        return v.lower()


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


# ─── Response schemas ─────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserMe(UserResponse):
    """Schema for /auth/me — same as UserResponse, kept separate for clarity."""
    pass


class UserListResponse(BaseModel):
    items: List[UserResponse]
    total: int
    page: int
    size: int
    pages: int
