"""
User service — business logic for user management (admin only).
"""

import math
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate, UserListResponse, UserResponse


class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)

    async def get_users(self, page: int = 1, size: int = 20) -> UserListResponse:
        skip = (page - 1) * size
        users = await self.user_repo.get_all(skip=skip, limit=size)
        total = await self.user_repo.count()
        pages = math.ceil(total / size) if total > 0 else 1
        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_user(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User dengan ID {user_id} tidak ditemukan",
            )
        return user

    async def create_user(self, data: UserCreate) -> User:
        # Check uniqueness
        if await self.user_repo.get_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Username '{data.username}' sudah digunakan",
            )
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{data.email}' sudah terdaftar",
            )

        user = User(
            username=data.username,
            email=data.email,
            full_name=data.full_name,
            role=data.role,
            hashed_password=hash_password(data.password),
            is_active=True,
        )
        return await self.user_repo.create(user)

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user(user_id)
        update_data = data.model_dump(exclude_none=True)

        # Check email uniqueness if being changed
        if "email" in update_data:
            existing = await self.user_repo.get_by_email(update_data["email"])
            if existing and existing.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{update_data['email']}' sudah digunakan",
                )

        return await self.user_repo.update(user, update_data)

    async def delete_user(self, user_id: int, requesting_user_id: int) -> None:
        if user_id == requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat menghapus akun sendiri",
            )
        user = await self.get_user(user_id)
        await self.user_repo.delete(user)

    async def toggle_active(self, user_id: int, requesting_user_id: int) -> User:
        if user_id == requesting_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat menonaktifkan akun sendiri",
            )
        user = await self.get_user(user_id)
        return await self.user_repo.update(user, {"is_active": not user.is_active})
