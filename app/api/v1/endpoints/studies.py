"""
Study endpoints — pemeriksaan radiologi.

Access control:
  GET    /studies        → semua role
  POST   /studies        → admin, radiolog
  GET    /studies/{id}   → semua role
  PATCH  /studies/{id}   → admin, radiolog
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.permissions import require_permission
from app.models.study import StudyStatus, Modality
from app.models.user import User
from app.schemas.study import (
    StudyCreate, StudyUpdate,
    StudyResponse, StudyListResponse,
)
from app.services.study_service import StudyService

router = APIRouter()


@router.get("", response_model=StudyListResponse, summary="Daftar pemeriksaan radiologi")
async def list_studies(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[StudyStatus] = Query(default=None, alias="status"),
    modality: Optional[Modality] = Query(default=None),
    patient_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("studies:read")),
):
    return await StudyService(db).get_studies(
        page=page, size=size,
        status_filter=status_filter, modality=modality, patient_id=patient_id,
    )


@router.post(
    "", response_model=StudyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Buat pemeriksaan baru",
)
async def create_study(
    data: StudyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("studies:create")),
):
    return await StudyService(db).create_study(data, created_by=current_user)


@router.get("/{study_id}", response_model=StudyResponse, summary="Detail pemeriksaan")
async def get_study(
    study_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("studies:read")),
):
    return await StudyService(db).get_study(study_id)


@router.patch(
    "/{study_id}", response_model=StudyResponse,
    summary="Update status / data pemeriksaan",
)
async def update_study(
    study_id: int,
    data: StudyUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("studies:update")),
):
    return await StudyService(db).update_study(study_id, data)
