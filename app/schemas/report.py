"""
Pydantic schemas for Report — request/response DTOs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, model_validator

from app.models.report import ReportStatus, ReportPriority


class ReportCreate(BaseModel):
    study_id: int
    findings: str
    impression: str
    technique: Optional[str] = None
    recommendation: Optional[str] = None
    internal_notes: Optional[str] = None
    priority: ReportPriority = ReportPriority.ROUTINE


class ReportUpdate(BaseModel):
    findings: Optional[str] = None
    impression: Optional[str] = None
    technique: Optional[str] = None
    recommendation: Optional[str] = None
    internal_notes: Optional[str] = None
    priority: Optional[ReportPriority] = None
    status: Optional[ReportStatus] = None
    amendment_reason: Optional[str] = None


class FinalizeReport(BaseModel):
    """Payload untuk finalisasi laporan."""
    verified_by_id: Optional[int] = None


class StudySummary(BaseModel):
    id: int
    accession_number: str
    modality: str
    body_part: str
    status: str
    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    id: int
    full_name: str
    role: str
    model_config = {"from_attributes": True}


class ReportResponse(BaseModel):
    id: int
    report_number: str
    study_id: int
    radiologist_id: int
    verified_by_id: Optional[int] = None
    technique: Optional[str] = None
    findings: str
    impression: str
    recommendation: Optional[str] = None
    internal_notes: Optional[str] = None
    status: ReportStatus
    priority: ReportPriority
    drafted_at: Optional[datetime] = None
    finalized_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    amended_at: Optional[datetime] = None
    amendment_reason: Optional[str] = None
    study: Optional[StudySummary] = None
    radiologist: Optional[UserSummary] = None
    verified_by: Optional[UserSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    items: List[ReportResponse]
    total: int
    page: int
    size: int
    pages: int
