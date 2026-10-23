"""
Report repository — data access layer for Report model.
"""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportStatus
from app.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self, db: AsyncSession):
        super().__init__(Report, db)

    async def get_by_id_with_relations(self, id: int) -> Optional[Report]:
        result = await self.db.execute(
            select(Report)
            .options(
                selectinload(Report.study),
                selectinload(Report.radiologist),
                selectinload(Report.verified_by),
            )
            .where(Report.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_study_id(self, study_id: int) -> Optional[Report]:
        result = await self.db.execute(
            select(Report).where(Report.study_id == study_id)
        )
        return result.scalar_one_or_none()

    async def get_all_with_relations(
        self, skip: int = 0, limit: int = 20,
        status: Optional[ReportStatus] = None,
        radiologist_id: Optional[int] = None,
    ) -> list[Report]:
        q = (
            select(Report)
            .options(
                selectinload(Report.study),
                selectinload(Report.radiologist),
                selectinload(Report.verified_by),
            )
            .order_by(Report.created_at.desc())
        )
        if status:
            q = q.where(Report.status == status)
        if radiologist_id:
            q = q.where(Report.radiologist_id == radiologist_id)
        q = q.offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        status: Optional[ReportStatus] = None,
        radiologist_id: Optional[int] = None,
    ) -> int:
        q = select(func.count()).select_from(Report)
        if status:
            q = q.where(Report.status == status)
        if radiologist_id:
            q = q.where(Report.radiologist_id == radiologist_id)
        result = await self.db.execute(q)
        return result.scalar_one()

    async def count_pending(self) -> int:
        """Jumlah laporan yang belum difinalisasi."""
        result = await self.db.execute(
            select(func.count()).select_from(Report)
            .where(Report.status.in_([ReportStatus.DRAFT, ReportStatus.PENDING_REVIEW]))
        )
        return result.scalar_one()

    async def generate_report_number(self) -> str:
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        result = await self.db.execute(select(func.count()).select_from(Report))
        count = result.scalar_one()
        return f"RPT-{today}-{str(count + 1).zfill(6)}"
