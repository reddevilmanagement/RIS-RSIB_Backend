"""
Study model — pemeriksaan radiologi (satu sesi imaging per pasien).

Alur: Appointment → Study → Report
Terminologi DICOM digunakan agar kompatibel dengan standar radiologi internasional.
"""

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.user import User
    from app.models.report import Report
    from app.models.appointment import Appointment


class Modality(str, enum.Enum):
    """Jenis modalitas alat radiologi (standar DICOM)."""
    CR  = "CR"   # Computed Radiography (Rontgen digital)
    DX  = "DX"   # Digital X-Ray
    CT  = "CT"   # Computed Tomography
    MR  = "MR"   # Magnetic Resonance Imaging
    US  = "US"   # Ultrasonography
    MG  = "MG"   # Mammography
    NM  = "NM"   # Nuclear Medicine
    PT  = "PT"   # PET Scan
    XA  = "XA"   # X-Ray Angiography
    RF  = "RF"   # Radiofluoroscopy


class StudyStatus(str, enum.Enum):
    """Status alur kerja pemeriksaan."""
    SCHEDULED   = "scheduled"    # Terjadwal, belum dilakukan
    IN_PROGRESS = "in_progress"  # Sedang dilakukan
    COMPLETED   = "completed"    # Selesai, menunggu laporan
    REPORTED    = "reported"     # Laporan sudah dibuat
    CANCELLED   = "cancelled"    # Dibatalkan


class Study(TimestampMixin, Base):
    """
    Satu sesi pemeriksaan radiologi.
    Satu pasien bisa memiliki banyak study.
    Satu study menghasilkan satu report.
    """

    __tablename__ = "studies"

    # ─── Primary Key ──────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ─── Identifikasi ─────────────────────────────────────────────────
    # Nomor unik pemeriksaan (format: STD-YYYYMMDD-XXXXXX)
    study_instance_uid: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )
    accession_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )

    # ─── Foreign Keys ─────────────────────────────────────────────────
    patient_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    appointment_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    referring_doctor_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    performing_radiologist_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ─── Detail Pemeriksaan ───────────────────────────────────────────
    modality: Mapped[Modality] = mapped_column(
        Enum(Modality, name="modality"), nullable=False, index=True
    )
    body_part: Mapped[str] = mapped_column(String(100), nullable=False)
    # Deskripsi klinis / indikasi dari dokter pengirim
    clinical_indication: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Prosedur spesifik (misal: "Thorax PA", "CT Kepala tanpa kontras")
    procedure_description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # ─── Status & Waktu ───────────────────────────────────────────────
    status: Mapped[StudyStatus] = mapped_column(
        Enum(StudyStatus, name="studystatus"),
        default=StudyStatus.SCHEDULED,
        nullable=False,
        index=True,
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ─── Catatan ──────────────────────────────────────────────────────
    technician_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Relationships ────────────────────────────────────────────────
    patient: Mapped["Patient"] = relationship("Patient", back_populates="studies")
    appointment: Mapped[Optional["Appointment"]] = relationship(
        "Appointment", back_populates="study"
    )
    referring_doctor: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[referring_doctor_id], back_populates="referred_studies"
    )
    performing_radiologist: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[performing_radiologist_id], back_populates="performed_studies"
    )
    report: Mapped[Optional["Report"]] = relationship(
        "Report", back_populates="study", uselist=False, cascade="all, delete-orphan"
    )

    # ─── Composite Indexes ────────────────────────────────────────────
    __table_args__ = (
        Index("ix_studies_patient_status", "patient_id", "status"),
        Index("ix_studies_modality_status", "modality", "status"),
        Index("ix_studies_scheduled_at", "scheduled_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Study id={self.id} accession={self.accession_number} "
            f"modality={self.modality} status={self.status}>"
        )
