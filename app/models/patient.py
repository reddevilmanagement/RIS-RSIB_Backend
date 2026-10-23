"""
Patient model — data pasien yang terdaftar di sistem RIS.
"""

import enum
from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Date, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.appointment import Appointment


class Gender(str, enum.Enum):
    LAKI_LAKI = "L"
    PEREMPUAN = "P"


class Patient(TimestampMixin, Base):
    """Pasien terdaftar dalam sistem."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    medical_record_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    nik: Mapped[Optional[str]] = mapped_column(String(16), unique=True, nullable=True)
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="gender"), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    blood_type: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Relationships ────────────────────────────────────────────────
    studies: Mapped[List["Study"]] = relationship(
        "Study", back_populates="patient", cascade="all, delete-orphan", lazy="select"
    )
    appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment", back_populates="patient", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Patient id={self.id} mrn={self.medical_record_number} name={self.full_name}>"
