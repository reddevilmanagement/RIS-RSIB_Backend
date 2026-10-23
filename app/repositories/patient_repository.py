"""
Patient repository — data access layer for Patient model.
"""

from typing import Optional

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.repositories.base_repository import BaseRepository


class PatientRepository(BaseRepository[Patient]):
    def __init__(self, db: AsyncSession):
        super().__init__(Patient, db)

    async def get_by_mrn(self, mrn: str) -> Optional[Patient]:
        """Get patient by Medical Record Number."""
        result = await self.db.execute(
            select(Patient).where(Patient.medical_record_number == mrn)
        )
        return result.scalar_one_or_none()

    async def search(self, query: str, skip: int = 0, limit: int = 20) -> list[Patient]:
        """Search patients by name or MRN."""
        result = await self.db.execute(
            select(Patient)
            .where(
                or_(
                    Patient.full_name.ilike(f"%{query}%"),
                    Patient.medical_record_number.ilike(f"%{query}%"),
                )
            )
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def generate_mrn(self) -> str:
        """Generate a unique Medical Record Number."""
        result = await self.db.execute(select(func.count()).select_from(Patient))
        count = result.scalar_one()
        return f"MRN{str(count + 1).zfill(6)}"
