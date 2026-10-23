"""
Patient endpoints — CRUD operations for patient management.

Access control:
  GET    /patients        → admin, radiolog, dokter, resepsionis (all roles)
  POST   /patients        → admin, resepsionis
  GET    /patients/{id}   → admin, radiolog, dokter, resepsionis
  PATCH  /patients/{id}   → admin, resepsionis
  DELETE /patients/{id}   → admin only
"""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.permissions import (
    require_permission,
    require_admin,
    require_any_role,
    require_admin_or_resepsionis,
)
from app.models.user import User
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, PatientListResponse
from app.services.patient_service import PatientService

router = APIRouter()


@router.get(
    "",
    response_model=PatientListResponse,
    summary="Daftar pasien",
    description="Semua role dapat melihat daftar pasien.",
)
async def list_patients(
    page: int = Query(default=1, ge=1, description="Nomor halaman"),
    size: int = Query(default=20, ge=1, le=100, description="Jumlah item per halaman"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients:read")),
):
    return await PatientService(db).get_patients(page=page, size=size)


@router.post(
    "",
    response_model=PatientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Daftarkan pasien baru",
    description="Hanya admin dan resepsionis yang dapat mendaftarkan pasien baru.",
)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients:create")),
):
    return await PatientService(db).create_patient(data)


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Detail pasien",
    description="Semua role dapat melihat detail pasien.",
)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients:read")),
):
    return await PatientService(db).get_patient(patient_id)


@router.patch(
    "/{patient_id}",
    response_model=PatientResponse,
    summary="Update data pasien",
    description="Hanya admin dan resepsionis yang dapat mengubah data pasien.",
)
async def update_patient(
    patient_id: int,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients:update")),
):
    return await PatientService(db).update_patient(patient_id, data)


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Hapus pasien",
    description="Hanya admin yang dapat menghapus data pasien.",
)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("patients:delete")),
):
    await PatientService(db).delete_patient(patient_id)
