"""
Report model — laporan radiologi hasil interpretasi study.

Satu Study menghasilkan tepat satu Report.
Report memiliki alur: DRAFT → PENDING_REVIEW → FINALIZED (atau AMENDED).
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
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.user import User


class ReportStatus(str, enum.Enum):
    """Status alur kerja laporan radiologi."""
    DRAFT          = "draft"           # Sedang ditulis
    PENDING_REVIEW = "pending_review"  # Menunggu verifikasi senior
    FINALIZED      = "finalized"       # Ditandatangani, final
    AMENDED        = "amended"         # Direvisi setelah finalisasi


class ReportPriority(str, enum.Enum):
    """Prioritas laporan — mempengaruhi SLA penyelesaian."""
    ROUTINE  = "routine"   # Normal (24–48 jam)
    URGENT   = "urgent"    # Mendesak (4–8 jam)
    STAT     = "stat"      # Segera / darurat (< 1 jam)


class Report(TimestampMixin, Base):
    """
    Laporan radiologi — hasil interpretasi dari satu Study.
    Relasi: Study (1) ←→ (1) Report
    """

    __tablename__ = "reports"

    # ─── Primary Key ──────────────────────────────────────────────────
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # ─── Identifikasi ─────────────────────────────────────────────────
    report_number: Mapped[str] = mapped_column(
        String(20), unique=True, index=True, nullable=False
    )

    # ─── Foreign Keys ─────────────────────────────────────────────────
    study_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("studies.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,   # Satu study → satu report
        index=True,
    )
    # Radiolog yang menulis laporan
    radiologist_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Radiolog senior yang memverifikasi (opsional)
    verified_by_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ─── Konten Laporan ───────────────────────────────────────────────
    # Teknik pemeriksaan yang digunakan
    technique: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Temuan radiologi (deskripsi objektif)
    findings: Mapped[str] = mapped_column(Text, nullable=False)
    # Kesimpulan / diagnosis radiologi
    impression: Mapped[str] = mapped_column(Text, nullable=False)
    # Rekomendasi tindak lanjut (opsional)
    recommendation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Catatan internal (tidak tampil ke pasien)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ─── Klasifikasi ──────────────────────────────────────────────────
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="reportstatus"),
        default=ReportStatus.DRAFT,
        nullable=False,
        index=True,
    )
    priority: Mapped[ReportPriority] = mapped_column(
        Enum(ReportPriority, name="reportpriority"),
        default=ReportPriority.ROUTINE,
        nullable=False,
        index=True,
    )

    # ─── Timestamps Alur Kerja ────────────────────────────────────────
    # Waktu laporan mulai ditulis
    drafted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Waktu laporan difinalisasi / ditandatangani
    finalized_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Waktu laporan diverifikasi oleh senior
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Waktu amandemen terakhir
    amended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Alasan amandemen
    amendment_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # ─── Relationships ────────────────────────────────────────────────
    study: Mapped["Study"] = relationship("Study", back_populates="report")
    radiologist: Mapped["User"] = relationship(
        "User", foreign_keys=[radiologist_id], back_populates="authored_reports"
    )
    verified_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[verified_by_id]
    )

    # ─── Composite Indexes ────────────────────────────────────────────
    __table_args__ = (
        Index("ix_reports_radiologist_status", "radiologist_id", "status"),
        Index("ix_reports_status_priority", "status", "priority"),
        Index("ix_reports_finalized_at", "finalized_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Report id={self.id} number={self.report_number} "
            f"status={self.status} priority={self.priority}>"
        )
