"""
Pydantic schemas for Appointment — request/response DTOs.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, field_validator

from app.models.appointment import AppointmentStatus, AppointmentPriority


class AppointmentBase(BaseModel):
    patient_id: int
    requested_modality: str
    body_part: str
    scheduled_datetime: datetime
    clinical_indication: Optional[str] = None
    preparation_instructions: Optional[str] = None
    estimated_duration_minutes: int = 30
    priority: AppointmentPriority = AppointmentPriority.ROUTINE
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    referring_doctor_id: Optional[int] = None


class AppointmentUpdate(BaseModel):
    scheduled_datetime: Optional[datetime] = None
    requested_modality: Optional[str] = None
    body_part: Optional[str] = None
    clinical_indication: Optional[str] = None
    preparation_instructions: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    priority: Optional[AppointmentPriority] = None
    notes: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    cancellation_reason: Optional[str] = None
    checked_in_at: Optional[datetime] = None


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


class AppointmentResponse(AppointmentBase):
    id: int
    appointment_number: str
    status: AppointmentStatus
    referring_doctor_id: Optional[int] = None
    created_by_id: Optional[int] = None
    cancellation_reason: Optional[str] = None
    checked_in_at: Optional[datetime] = None
    patient: Optional[PatientSummary] = None
    referring_doctor: Optional[UserSummary] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AppointmentListResponse(BaseModel):
    items: List[AppointmentResponse]
    total: int
    page: int
    size: int
    pages: int
