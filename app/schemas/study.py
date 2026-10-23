"""
Pydantic schemas for Study — request/response DTOs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from app.models.study import Modality, StudyStatus


class StudyBase(BaseModel):
    patient_id: int
    modality: Modality
    body_part: str
    clinical_indication: Optional[str] = None
    procedure_description: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class StudyCreate(StudyBase):
    appointment_id: Optional[int] = None
    referring_doctor_id: Optional[int] = None
    performing_radiologist_id: Optional[int] = None


class StudyUpdate(BaseModel):
    status: Optional[StudyStatus] = None
    performing_radiologist_id: Optional[int] = None
    procedure_description: Optional[str] = None
    clinical_indication: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    technician_notes: Optional[str] = None


class PatientSummary(BaseModel):
    id: int
    full_name: str
    medical_record_number: str
    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    id: int
    full_name: str
    role: str
    model_config = {"from_attributes": True}


class StudyResponse(StudyBase):
    id: int
    study_instance_uid: str
    accession_number: str
    status: StudyStatus
    appointment_id: Optional[int] = None
    referring_doctor_id: Optional[int] = None
    performing_radiologist_id: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    technician_notes: Optional[str] = None
    patient: Optional[PatientSummary] = None
    referring_doctor: Optional[UserSummary] = None
    performing_radiologist: Optional[UserSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StudyListResponse(BaseModel):
    items: List[StudyResponse]
    total: int
    page: int
    size: int
    pages: int
