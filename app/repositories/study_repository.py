"""
Study repository — data access layer for Study model.
"""

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study import Study, StudyStatus, Modality
from app.repositories.base_repository import BaseRepository


class StudyRepository(BaseRepository[Study]):
    def __init__(self, db: AsyncSession):
        super().__init__(Study, db)

    async def get_by_id_with_relations(self, id: int) -> Optional[Study]:
        result = await self.db.execute(
            select(Study)
            .options(
                selectinload(Study.patient),
                selectinload(Study.referring_doctor),
                selectinload(Study.performing_radiologist),
                selectinload(Study.report),
            )
            .where(Study.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self, skip: int = 0, limit: int = 20,
        status: Optional[StudyStatus] = None,
        modality: Optional[Modality] = None,
        patient_id: Optional[int] = None,
    ) -> list[Study]:
        q = (
            select(Study)
            .options(
                selectinload(Study.patient),
                selectinload(Study.referring_doctor),
                selectinload(Study.performing_radiologist),
            )
            .order_by(Study.created_at.desc())
        )
        if status:
            q = q.where(Study.status == status)
        if modality:
            q = q.where(Study.modality == modality)
        if patient_id:
            q = q.where(Study.patient_id == patient_id)
        q = q.offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        status: Optional[StudyStatus] = None,
        modality: Optional[Modality] = None,
        patient_id: Optional[int] = None,
    ) -> int:
        q = select(func.count()).select_from(Study)
        if status:
            q = q.where(Study.status == status)
        if modality:
            q = q.where(Study.modality == modality)
        if patient_id:
            q = q.where(Study.patient_id == patient_id)
        result = await self.db.execute(q)
        return result.scalar_one()

    async def count_today(self) -> int:
        """Jumlah study yang dijadwalkan hari ini."""
        today = datetime.now(timezone.utc).date()
        start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        result = await self.db.execute(
            select(func.count()).select_from(Study)
            .where(and_(
                Study.created_at >= start,
                Study.created_at <= end,
                Study.status.notin_([StudyStatus.CANCELLED]),
            ))
        )
        return result.scalar_one()

    async def count_completed_today(self) -> int:
        today = datetime.now(timezone.utc).date()
        start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        end = datetime(today.year, today.month, today.day, 23, 59, 59, tzinfo=timezone.utc)
        result = await self.db.execute(
            select(func.count()).select_from(Study)
            .where(and_(
                Study.completed_at >= start,
                Study.completed_at <= end,
                Study.status.in_([StudyStatus.COMPLETED, StudyStatus.REPORTED]),
            ))
        )
        return result.scalar_one()

    async def generate_accession_number(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        result = await self.db.execute(select(func.count()).select_from(Study))
        count = result.scalar_one()
        return f"STD-{today}-{str(count + 1).zfill(6)}"

    async def generate_study_instance_uid(self) -> str:
        return f"2.25.{uuid.uuid4().int}"
