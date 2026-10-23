"""
User management endpoints — admin-only CRUD + self-service profile.

Access control:
  GET    /users          → admin only
  POST   /users          → admin only
  GET    /users/{id}     → admin only
  PATCH  /users/{id}     → admin only
  DELETE /users/{id}     → admin only
  POST   /users/{id}/toggle-active → admin only
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.permissions import require_admin
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserListResponse
from app.services.user_service import UserService

router = APIRouter()


@router.get(
    "",
    response_model=UserListResponse,
    summary="Daftar semua pengguna",
    description="Hanya admin yang dapat melihat daftar seluruh pengguna sistem.",
)
async def list_users(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService(db).get_users(page=page, size=size)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat pengguna baru",
    description="Hanya admin yang dapat membuat akun pengguna baru.",
)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService(db).create_user(data)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Detail pengguna",
    description="Hanya admin yang dapat melihat detail pengguna lain.",
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService(db).get_user(user_id)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update pengguna",
    description="Hanya admin yang dapat mengubah data pengguna.",
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await UserService(db).update_user(user_id, data)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus pengguna",
    description="Hanya admin yang dapat menghapus pengguna. Admin tidak dapat menghapus dirinya sendiri.",
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await UserService(db).delete_user(user_id, requesting_user_id=current_user.id)


@router.post(
    "/{user_id}/toggle-active",
    response_model=UserResponse,
    summary="Aktifkan / nonaktifkan pengguna",
    description="Toggle status aktif pengguna. Admin tidak dapat menonaktifkan dirinya sendiri.",
)
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    return await UserService(db).toggle_active(user_id, requesting_user_id=current_user.id)
