"""
Patient service — business logic for patient management.
"""

import math
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patient import Patient
from app.repositories.patient_repository import PatientRepository
from app.schemas.patient import PatientCreate, PatientUpdate, PatientListResponse, PatientResponse


class PatientService:
    def __init__(self, db: AsyncSession):
        self.patient_repo = PatientRepository(db)

    async def get_patients(self, page: int = 1, size: int = 20) -> PatientListResponse:
        """Get paginated list of patients."""
        skip = (page - 1) * size
        patients = await self.patient_repo.get_all(skip=skip, limit=size)
        total = await self.patient_repo.count()
        pages = math.ceil(total / size) if total > 0 else 1

        return PatientListResponse(
            items=[PatientResponse.model_validate(p) for p in patients],
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    async def get_patient(self, patient_id: int) -> Patient:
        """Get a single patient by ID."""
        patient = await self.patient_repo.get_by_id(patient_id)
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pasien dengan ID {patient_id} tidak ditemukan",
            )
        return patient

    async def create_patient(self, data: PatientCreate) -> Patient:
        """Register a new patient."""
        mrn = await self.patient_repo.generate_mrn()
        patient = Patient(**data.model_dump(), medical_record_number=mrn)
        return await self.patient_repo.create(patient)

    async def update_patient(self, patient_id: int, data: PatientUpdate) -> Patient:
        """Update patient information."""
        patient = await self.get_patient(patient_id)
        return await self.patient_repo.update(patient, data.model_dump(exclude_none=True))

    async def delete_patient(self, patient_id: int) -> None:
        """Delete a patient record."""
        patient = await self.get_patient(patient_id)
        await self.patient_repo.delete(patient)
