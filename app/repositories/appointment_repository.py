"""
Appointment repository — data access layer for Appointment model.
"""

from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.appointment import Appointment, AppointmentStatus
from app.repositories.base_repository import BaseRepository


class AppointmentRepository(BaseRepository[Appointment]):
    def __init__(self, db: AsyncSession):
        super().__init__(Appointment, db)

    async def get_by_id_with_relations(self, id: int) -> Optional[Appointment]:
        result = await self.db.execute(
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.referring_doctor),
                selectinload(Appointment.created_by),
            )
            .where(Appointment.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self, skip: int = 0, limit: int = 20,
        status: Optional[AppointmentStatus] = None,
        patient_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> list[Appointment]:
        q = (
            select(Appointment)
            .options(
                selectinload(Appointment.patient),
                selectinload(Appointment.referring_doctor),
            )
            .order_by(Appointment.scheduled_datetime.asc())
        )
        if status:
            q = q.where(Appointment.status == status)
        if patient_id:
            q = q.where(Appointment.patient_id == patient_id)
        if date_from:
            q = q.where(Appointment.scheduled_datetime >= datetime(date_from.year, date_from.month, date_from.day, tzinfo=timezone.utc))
        if date_to:
            q = q.where(Appointment.scheduled_datetime < datetime(date_to.year, date_to.month, date_to.day + 1, tzinfo=timezone.utc))
        q = q.offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        status: Optional[AppointmentStatus] = None,
        patient_id: Optional[int] = None,
    ) -> int:
        q = select(func.count()).select_from(Appointment)
        if status:
            q = q.where(Appointment.status == status)
        if patient_id:
            q = q.where(Appointment.patient_id == patient_id)
        result = await self.db.execute(q)
        return result.scalar_one()

    async def count_today(self) -> int:
        today = datetime.now(timezone.utc).date()
        start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        result = await self.db.execute(
            select(func.count()).select_from(Appointment)
            .where(and_(
                Appointment.scheduled_datetime >= start,
                Appointment.scheduled_datetime <= end,
                Appointment.status.notin_([AppointmentStatus.CANCELLED]),
            ))
        )
        return result.scalar_one()

    async def generate_appointment_number(self) -> str:
        from datetime import date as dt
        today = dt.today().strftime("%Y%m%d")
        result = await self.db.execute(select(func.count()).select_from(Appointment))
        count = result.scalar_one()
        return f"APT-{today}-{str(count + 1).zfill(4)}"
