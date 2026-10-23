"""
Report service — business logic for radiology report management.
"""

import math
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report import Report, ReportStatus
from app.models.study import StudyStatus
from app.models.user import User, UserRole
from app.repositories.report_repository import ReportRepository
from app.repositories.study_repository import StudyRepository
from app.schemas.report import ReportCreate, ReportUpdate, ReportResponse, ReportListResponse


class ReportService:
    def __init__(self, db: AsyncSession):
        self.repo = ReportRepository(db)
        self.study_repo = StudyRepository(db)

    async def get_reports(
        self,
        page: int = 1,
        size: int = 20,
        status_filter: Optional[ReportStatus] = None,
        radiologist_id: Optional[int] = None,
    ) -> ReportListResponse:
        skip = (page - 1) * size
        items = await self.repo.get_all_with_relations(
            skip=skip, limit=size,
            status=status_filter, radiologist_id=radiologist_id,
        )
        total = await self.repo.count_filtered(
            status=status_filter, radiologist_id=radiologist_id,
        )
        pages = math.ceil(total / size) if total > 0 else 1
        return ReportListResponse(
            items=[ReportResponse.model_validate(r) for r in items],
            total=total, page=page, size=size, pages=pages,
        )

    async def get_report(self, report_id: int) -> Report:
        report = await self.repo.get_by_id_with_relations(report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Laporan dengan ID {report_id} tidak ditemukan",
            )
        return report

    async def create_report(self, data: ReportCreate, author: User) -> Report:
        # Pastikan study ada dan statusnya COMPLETED
        study = await self.study_repo.get_by_id(data.study_id)
        if not study:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pemeriksaan dengan ID {data.study_id} tidak ditemukan",
            )
        if study.status != StudyStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pemeriksaan harus berstatus 'completed' sebelum laporan dibuat (saat ini: '{study.status}')",
            )

        # Cek apakah laporan sudah ada
        existing = await self.repo.get_by_study_id(data.study_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Laporan untuk pemeriksaan ini sudah ada",
            )

        number = await self.repo.generate_report_number()
        now = datetime.now(timezone.utc)
        report = Report(
            **data.model_dump(),
            report_number=number,
            radiologist_id=author.id,
            status=ReportStatus.DRAFT,
            drafted_at=now,
        )
        return await self.repo.create(report)

    async def update_report(self, report_id: int, data: ReportUpdate, user: User) -> Report:
        report = await self.get_report(report_id)

        # Hanya penulis atau admin yang bisa edit
        if report.radiologist_id != user.id and user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Hanya penulis laporan atau admin yang dapat mengedit",
            )

        if report.status == ReportStatus.FINALIZED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Laporan yang sudah difinalisasi tidak dapat diedit. Gunakan amandemen.",
            )

        update_data = data.model_dump(exclude_none=True)
        new_status = update_data.get("status")

        if new_status == ReportStatus.PENDING_REVIEW:
            pass  # valid transition dari DRAFT
        elif new_status == ReportStatus.FINALIZED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gunakan endpoint /finalize untuk memfinalisasi laporan",
            )

        return await self.repo.update(report, update_data)

    async def finalize_report(
        self, report_id: int, verifier: User, verified_by_id: Optional[int] = None
    ) -> Report:
        report = await self.get_report(report_id)

        if report.status not in [ReportStatus.DRAFT, ReportStatus.PENDING_REVIEW]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Laporan dengan status '{report.status}' tidak dapat difinalisasi",
            )

        # Verifikator tidak boleh sama dengan penulis
        effective_verifier_id = verified_by_id or verifier.id
        if effective_verifier_id == report.radiologist_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Penulis laporan tidak dapat memverifikasi laporannya sendiri",
            )

        now = datetime.now(timezone.utc)
        result = await self.repo.update(report, {
            "status": ReportStatus.FINALIZED,
            "verified_by_id": effective_verifier_id,
            "finalized_at": now,
            "verified_at": now,
        })

        # Update study status ke REPORTED
        study = await self.study_repo.get_by_id(report.study_id)
        if study:
            await self.study_repo.update(study, {"status": StudyStatus.REPORTED})

        return result

    async def amend_report(
        self, report_id: int, reason: str, user: User
    ) -> Report:
        report = await self.get_report(report_id)

        if report.status != ReportStatus.FINALIZED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Hanya laporan yang sudah difinalisasi yang dapat diamandemen",
            )

        return await self.repo.update(report, {
            "status": ReportStatus.AMENDED,
            "amendment_reason": reason,
            "amended_at": datetime.now(timezone.utc),
        })
