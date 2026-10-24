"""
User model — represents system users (admin, dokter, radiolog, dll).
"""

import enum
from typing import TYPE_CHECKING, List
from sqlalchemy import Boolean, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.models.base_model import TimestampMixin

if TYPE_CHECKING:
    from app.models.study import Study
    from app.models.report import Report
    from app.models.appointment import Appointment


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    DOKTER = "dokter"
    RADIOLOG = "radiolog"
    RESEPSIONIS = "resepsionis"


class User(TimestampMixin, Base):
    """System user account."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="userrole"), default=UserRole.RESEPSIONIS, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # ─── Relationships ────────────────────────────────────────────────
    # Studies this user referred (as dokter)
    referred_studies: Mapped[List["Study"]] = relationship(
        "Study",
        foreign_keys="Study.referring_doctor_id",
        back_populates="referring_doctor",
        lazy="select",
    )
    # Studies this user performed (as radiolog)
    performed_studies: Mapped[List["Study"]] = relationship(
        "Study",
        foreign_keys="Study.performing_radiologist_id",
        back_populates="performing_radiologist",
        lazy="select",
    )
    # Reports authored by this user
    authored_reports: Mapped[List["Report"]] = relationship(
        "Report",
        foreign_keys="Report.radiologist_id",
        back_populates="radiologist",
        lazy="select",
    )
    # Appointments created by this user (resepsionis)
    created_appointments: Mapped[List["Appointment"]] = relationship(
        "Appointment",
        foreign_keys="Appointment.created_by_id",
        back_populates="created_by",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username} role={self.role}>"
