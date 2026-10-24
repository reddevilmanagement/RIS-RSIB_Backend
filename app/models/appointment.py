"""
Appointment model — jadwal pemeriksaan radiologi.

Alur: Appointment (terjadwal) → Study (dilaksanakan) → Report (dilaporkan)
Satu appointment menghasilkan tepat satu study setelah dilaksanakan.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User
    from app.models.study import Study, Modality


class AppointmentStatus(str, enum.Enum):
    """Status janji pemeriksaan."""
    PENDING    = "pending"     # Menunggu konfirmasi
    CONFIRMED  = "confirmed"   # Dikonfirmasi
    CHECKED_IN = "checked_in"  # Pasien sudah hadir
    COMPLETED  = "completed"   # Selesai (study sudah dibuat)
    CANCELLED  = "cancelled"   # Dibatalkan
    NO_SHOW    = "no_show"     # Pasien tidak hadir


class AppointmentPriority(str, enum.Enum):
    """Prioritas jadwal."""
    ROUTINE   = "routine"
    URGENT    = "urgent"
    EMERGENCY = "emergency"


class Appointment(TimestampMixin, Base):
    """
    Jadwal pemeriksaan radiologi.
    Dibuat oleh resepsionis atas permintaan dokter.
    """

    __tablename__ = "appointments"

    # ─── Primary Key ──────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ─── Identifikasi ─────────────────────────────────────────────────
    appointment_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )

    # ─── Foreign Keys ─────────────────────────────────────────────────
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Dokter yang merujuk pasien untuk pemeriksaan
    referring_doctor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Resepsionis yang membuat jadwal
    created_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ─── Detail Jadwal ────────────────────────────────────────────────
    # Jenis modalitas yang diminta
    requested_modality: Mapped[str] = mapped_column(String(10), nullable=False)
    # Bagian tubuh yang akan diperiksa
    body_part: Mapped[str] = mapped_column(String(100), nullable=False)
    # Indikasi klinis dari dokter pengirim
    clinical_indication: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Instruksi persiapan untuk pasien (misal: puasa 6 jam)
    preparation_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Waktu ────────────────────────────────────────────────────────
    scheduled_datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    # Estimasi durasi dalam menit
    estimated_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # ─── Status & Prioritas ───────────────────────────────────────────
    status: Mapped[AppointmentStatus] = mapped_column(
        Enum(AppointmentStatus, name="appointmentstatus"),
        default=AppointmentStatus.PENDING,
        nullable=False,
        index=True,
    )
    priority: Mapped[AppointmentPriority] = mapped_column(
        Enum(AppointmentPriority, name="appointmentpriority"),
        default=AppointmentPriority.ROUTINE,
        nullable=False,
    )

    # ─── Catatan ──────────────────────────────────────────────────────
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Alasan pembatalan (diisi jika status = CANCELLED)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Waktu check-in pasien
    checked_in_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ─── Relationships ────────────────────────────────────────────────
    patient: Mapped["Patient"] = relationship("Patient", back_populates="appointments")
    referring_doctor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[referring_doctor_id]
    )
    created_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[created_by_id], back_populates="created_appointments"
    )
    # Study yang dihasilkan dari appointment ini (nullable sampai dilaksanakan)
    study: Mapped[Optional["Study"]] = relationship(
        "Study", back_populates="appointment", uselist=False
    )

    # ─── Composite Indexes ────────────────────────────────────────────
    __table_args__ = (
        Index("ix_appointments_patient_status", "patient_id", "status"),
        Index("ix_appointments_scheduled_datetime", "scheduled_datetime"),
        Index("ix_appointments_status_priority", "status", "priority"),
    )

    def __repr__(self) -> str:
        return (
            f"<Appointment id={self.id} number={self.appointment_number} "
            f"patient_id={self.patient_id} status={self.status}>"
        )
