"""
Report endpoints — laporan radiologi.

Access control:
  GET    /reports           → semua role kecuali resepsionis
  POST   /reports           → admin, radiolog
  GET    /reports/{id}      → semua role kecuali resepsionis
  PATCH  /reports/{id}      → admin, radiolog (penulis saja)
  POST   /reports/{id}/finalize → admin, radiolog
  POST   /reports/{id}/amend   → admin, radiolog
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, Body, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.models.report import ReportStatus
from app.models.user import User
from app.schemas.report import (
    ReportCreate, ReportUpdate, FinalizeReport,
    ReportResponse, ReportListResponse,
)
from app.services.report_service import ReportService

router = APIRouter()


@router.get("", response_model=ReportListResponse, summary="Daftar laporan radiologi")
async def list_reports(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ReportStatus] = Query(default=None, alias="status"),
    radiologist_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
):
    return await ReportService(db).get_reports(
        page=page, size=size,
        status_filter=status_filter, radiologist_id=radiologist_id,
    )


@router.post(
    "", response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat laporan radiologi baru",
)
async def create_report(
    data: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:create")),
):
    return await ReportService(db).create_report(data, author=current_user)


@router.get("/{report_id}", response_model=ReportResponse, summary="Detail laporan")
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("reports:read")),
):
    return await ReportService(db).get_report(report_id)


@router.patch(
    "/{report_id}", response_model=ReportResponse,
    summary="Update isi laporan (hanya penulis atau admin)",
)
async def update_report(
    report_id: int,
    data: ReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:update")),
):
    return await ReportService(db).update_report(report_id, data, user=current_user)


@router.post(
    "/{report_id}/finalize", response_model=ReportResponse,
    summary="Finalisasi laporan (tanda tangan digital)",
)
async def finalize_report(
    report_id: int,
    body: FinalizeReport = Body(default=FinalizeReport()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:update")),
):
    return await ReportService(db).finalize_report(
        report_id, verifier=current_user, verified_by_id=body.verified_by_id
    )


@router.post(
    "/{report_id}/amend", response_model=ReportResponse,
    summary="Amandemen laporan yang sudah difinalisasi",
)
async def amend_report(
    report_id: int,
    reason: str = Body(..., embed=True, description="Alasan amandemen"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("reports:update")),
):
    return await ReportService(db).amend_report(report_id, reason=reason, user=current_user)
