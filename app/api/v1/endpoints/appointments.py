"""
Appointment endpoints — jadwal pemeriksaan radiologi.

Access control:
  GET    /appointments        → semua role
  POST   /appointments        → admin, resepsionis, dokter
  GET    /appointments/{id}   → semua role
  PATCH  /appointments/{id}   → admin, resepsionis
  POST   /appointments/{id}/cancel → admin, resepsionis
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.permissions import require_permission, require_admin_or_resepsionis
from app.models.appointment import AppointmentStatus
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate,
    AppointmentResponse, AppointmentListResponse,
)
from app.services.appointment_service import AppointmentService

router = APIRouter()


@router.get("", response_model=AppointmentListResponse, summary="Daftar jadwal pemeriksaan")
async def list_appointments(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[AppointmentStatus] = Query(default=None, alias="status"),
    patient_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("appointments:read")),
):
    return await AppointmentService(db).get_appointments(
        page=page, size=size,
        status_filter=status_filter, patient_id=patient_id,
    )


@router.post(
    "", response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat jadwal pemeriksaan baru",
)
async def create_appointment(
    data: AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("appointments:create")),
):
    return await AppointmentService(db).create_appointment(data, created_by=current_user)


@router.get("/{appointment_id}", response_model=AppointmentResponse, summary="Detail jadwal")
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("appointments:read")),
):
    return await AppointmentService(db).get_appointment(appointment_id)


@router.patch(
    "/{appointment_id}", response_model=AppointmentResponse,
    summary="Update jadwal pemeriksaan",
)
async def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("appointments:update")),
):
    return await AppointmentService(db).update_appointment(appointment_id, data)


@router.post(
    "/{appointment_id}/cancel", response_model=AppointmentResponse,
    summary="Batalkan jadwal pemeriksaan",
)
async def cancel_appointment(
    appointment_id: int,
    reason: Optional[str] = Query(default=None, description="Alasan pembatalan"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("appointments:update")),
):
    return await AppointmentService(db).cancel_appointment(appointment_id, reason=reason)
