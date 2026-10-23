"""
Appointment service — business logic for appointment management.
"""

import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.models.user import User
from app.repositories.appointment_repository import AppointmentRepository
from app.schemas.appointment import (
    AppointmentCreate, AppointmentUpdate,
    AppointmentResponse, AppointmentListResponse,
)


class AppointmentService:
    def __init__(self, db: AsyncSession):
        self.repo = AppointmentRepository(db)

    async def get_appointments(
        self,
        page: int = 1,
        size: int = 20,
        status_filter: Optional[AppointmentStatus] = None,
        patient_id: Optional[int] = None,
    ) -> AppointmentListResponse:
        skip = (page - 1) * size
        items = await self.repo.get_all_with_relations(
            skip=skip, limit=size,
            status=status_filter, patient_id=patient_id,
        )
        total = await self.repo.count_filtered(status=status_filter, patient_id=patient_id)
        pages = math.ceil(total / size) if total > 0 else 1
        return AppointmentListResponse(
            items=[AppointmentResponse.model_validate(a) for a in items],
            total=total, page=page, size=size, pages=pages,
        )

    async def get_appointment(self, appointment_id: int) -> Appointment:
        appt = await self.repo.get_by_id_with_relations(appointment_id)
        if not appt:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Jadwal dengan ID {appointment_id} tidak ditemukan",
            )
        return appt

    async def create_appointment(
        self, data: AppointmentCreate, created_by: User
    ) -> Appointment:
        number = await self.repo.generate_appointment_number()
        appt = Appointment(
            **data.model_dump(),
            appointment_number=number,
            created_by_id=created_by.id,
            status=AppointmentStatus.PENDING,
        )
        return await self.repo.create(appt)

    async def update_appointment(
        self, appointment_id: int, data: AppointmentUpdate
    ) -> Appointment:
        appt = await self.get_appointment(appointment_id)

        # Validasi transisi status
        update_data = data.model_dump(exclude_none=True)
        new_status = update_data.get("status")

        if new_status:
            self._validate_status_transition(appt.status, new_status)

        # Set checked_in_at otomatis
        if new_status == AppointmentStatus.CHECKED_IN and not update_data.get("checked_in_at"):
            update_data["checked_in_at"] = datetime.now(timezone.utc)

        return await self.repo.update(appt, update_data)

    async def cancel_appointment(
        self, appointment_id: int, reason: Optional[str] = None
    ) -> Appointment:
        appt = await self.get_appointment(appointment_id)
        if appt.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Jadwal dengan status '{appt.status}' tidak dapat dibatalkan",
            )
        return await self.repo.update(appt, {
            "status": AppointmentStatus.CANCELLED,
            "cancellation_reason": reason,
        })

    def _validate_status_transition(
        self, current: AppointmentStatus, new: AppointmentStatus
    ) -> None:
        allowed: dict[AppointmentStatus, list[AppointmentStatus]] = {
            AppointmentStatus.PENDING:    [AppointmentStatus.CONFIRMED, AppointmentStatus.CANCELLED],
            AppointmentStatus.CONFIRMED:  [AppointmentStatus.CHECKED_IN, AppointmentStatus.CANCELLED, AppointmentStatus.NO_SHOW],
            AppointmentStatus.CHECKED_IN: [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED],
            AppointmentStatus.COMPLETED:  [],
            AppointmentStatus.CANCELLED:  [],
            AppointmentStatus.NO_SHOW:    [],
        }
        if new not in allowed.get(current, []):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tidak dapat mengubah status dari '{current}' ke '{new}'",
            )
