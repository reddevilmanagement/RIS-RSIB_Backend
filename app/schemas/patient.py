"""
Pydantic schemas for Patient — request/response DTOs.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

from app.models.patient import Gender


class PatientBase(BaseModel):
    full_name: str
    date_of_birth: date
    gender: Gender
    nik: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    address: Optional[str] = None
    blood_type: Optional[str] = None
    allergies: Optional[str] = None


class PatientResponse(PatientBase):
    id: int
    medical_record_number: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PatientListResponse(BaseModel):
    items: list[PatientResponse]
    total: int
    page: int
    size: int
    pages: int
