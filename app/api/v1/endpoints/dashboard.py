"""
Dashboard endpoints — real statistics for the main dashboard.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.models.user import User
from app.repositories.patient_repository import PatientRepository
from app.repositories.study_repository import StudyRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.appointment_repository import AppointmentRepository

router = APIRouter()


@router.get("/stats", summary="Statistik dashboard (real-time)")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("dashboard:read")),
):
    patient_repo     = PatientRepository(db)
    study_repo       = StudyRepository(db)
    report_repo      = ReportRepository(db)
    appointment_repo = AppointmentRepository(db)

    total_patients, studies_today, pending_reports, completed_today, appointments_today = (
        await patient_repo.count(),
        await study_repo.count_today(),
        await report_repo.count_pending(),
        await study_repo.count_completed_today(),
        await appointment_repo.count_today(),
    )

    return {
        "total_patients":            total_patients,
        "total_examinations_today":  studies_today,
        "pending_reports":           pending_reports,
        "completed_today":           completed_today,
        "appointments_today":        appointments_today,
    }
