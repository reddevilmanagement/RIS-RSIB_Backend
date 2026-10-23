"""Initial schema — users, patients, appointments, studies, reports

Revision ID: 0001
Revises:
Create Date: 2026-05-08
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ─── ENUM types ───────────────────────────────────────────────────
    userrole = postgresql.ENUM(
        "admin", "dokter", "radiolog", "resepsionis",
        name="userrole", create_type=True
    )
    gender = postgresql.ENUM("L", "P", name="gender", create_type=True)
    modality = postgresql.ENUM(
        "CR", "DX", "CT", "MR", "US", "MG", "NM", "PT", "XA", "RF",
        name="modality", create_type=True
    )
    studystatus = postgresql.ENUM(
        "scheduled", "in_progress", "completed", "reported", "cancelled",
        name="studystatus", create_type=True
    )
    reportstatus = postgresql.ENUM(
        "draft", "pending_review", "finalized", "amended",
        name="reportstatus", create_type=True
    )
    reportpriority = postgresql.ENUM(
        "routine", "urgent", "stat",
        name="reportpriority", create_type=True
    )
    appointmentstatus = postgresql.ENUM(
        "pending", "confirmed", "checked_in", "completed", "cancelled", "no_show",
        name="appointmentstatus", create_type=True
    )
    appointmentpriority = postgresql.ENUM(
        "routine", "urgent", "emergency",
        name="appointmentpriority", create_type=True
    )

    for enum_type in [
        userrole, gender, modality, studystatus,
        reportstatus, reportpriority, appointmentstatus, appointmentpriority
    ]:
        enum_type.create(op.get_bind(), checkfirst=True)

    # ─── users ────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("admin", "dokter", "radiolog", "resepsionis", name="userrole"), nullable=False, server_default="resepsionis"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_email", "users", ["email"])

    # ─── patients ─────────────────────────────────────────────────────
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("medical_record_number", sa.String(20), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("nik", sa.String(16), nullable=True, unique=True),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("gender", sa.Enum("L", "P", name="gender"), nullable=False),
        sa.Column("phone_number", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("blood_type", sa.String(5), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_patients_mrn", "patients", ["medical_record_number"])
    op.create_index("ix_patients_full_name", "patients", ["full_name"])

    # ─── appointments ─────────────────────────────────────────────────
    op.create_table(
        "appointments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("appointment_number", sa.String(20), nullable=False, unique=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("referring_doctor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requested_modality", sa.String(10), nullable=False),
        sa.Column("body_part", sa.String(100), nullable=False),
        sa.Column("clinical_indication", sa.Text(), nullable=True),
        sa.Column("preparation_instructions", sa.Text(), nullable=True),
        sa.Column("scheduled_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estimated_duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("status", sa.Enum("pending", "confirmed", "checked_in", "completed", "cancelled", "no_show", name="appointmentstatus"), nullable=False, server_default="pending"),
        sa.Column("priority", sa.Enum("routine", "urgent", "emergency", name="appointmentpriority"), nullable=False, server_default="routine"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("cancellation_reason", sa.String(500), nullable=True),
        sa.Column("checked_in_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_scheduled_datetime", "appointments", ["scheduled_datetime"])
    op.create_index("ix_appointments_status", "appointments", ["status"])
    op.create_index("ix_appointments_patient_status", "appointments", ["patient_id", "status"])

    # ─── studies ──────────────────────────────────────────────────────
    op.create_table(
        "studies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("study_instance_uid", sa.String(64), nullable=False, unique=True),
        sa.Column("accession_number", sa.String(20), nullable=False, unique=True),
        sa.Column("patient_id", sa.Integer(), sa.ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("appointment_id", sa.Integer(), sa.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("referring_doctor_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("performing_radiologist_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("modality", sa.Enum("CR", "DX", "CT", "MR", "US", "MG", "NM", "PT", "XA", "RF", name="modality"), nullable=False),
        sa.Column("body_part", sa.String(100), nullable=False),
        sa.Column("clinical_indication", sa.Text(), nullable=True),
        sa.Column("procedure_description", sa.String(255), nullable=True),
        sa.Column("status", sa.Enum("scheduled", "in_progress", "completed", "reported", "cancelled", name="studystatus"), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("technician_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_studies_patient_id", "studies", ["patient_id"])
    op.create_index("ix_studies_accession_number", "studies", ["accession_number"])
    op.create_index("ix_studies_modality", "studies", ["modality"])
    op.create_index("ix_studies_status", "studies", ["status"])
    op.create_index("ix_studies_scheduled_at", "studies", ["scheduled_at"])
    op.create_index("ix_studies_patient_status", "studies", ["patient_id", "status"])
    op.create_index("ix_studies_modality_status", "studies", ["modality", "status"])

    # ─── reports ──────────────────────────────────────────────────────
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_number", sa.String(20), nullable=False, unique=True),
        sa.Column("study_id", sa.Integer(), sa.ForeignKey("studies.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("radiologist_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("verified_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("technique", sa.Text(), nullable=True),
        sa.Column("findings", sa.Text(), nullable=False),
        sa.Column("impression", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column("status", sa.Enum("draft", "pending_review", "finalized", "amended", name="reportstatus"), nullable=False, server_default="draft"),
        sa.Column("priority", sa.Enum("routine", "urgent", "stat", name="reportpriority"), nullable=False, server_default="routine"),
        sa.Column("drafted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("amendment_reason", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "verified_by_id IS NULL OR verified_by_id != radiologist_id",
            name="chk_reports_verifier"
        ),
    )
    op.create_index("ix_reports_study_id", "reports", ["study_id"])
    op.create_index("ix_reports_radiologist_id", "reports", ["radiologist_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_priority", "reports", ["priority"])
    op.create_index("ix_reports_finalized_at", "reports", ["finalized_at"])
    op.create_index("ix_reports_radiologist_status", "reports", ["radiologist_id", "status"])
    op.create_index("ix_reports_status_priority", "reports", ["status", "priority"])


def downgrade() -> None:
    op.drop_table("reports")
    op.drop_table("studies")
    op.drop_table("appointments")
    op.drop_table("patients")
    op.drop_table("users")

    for enum_name in [
        "appointmentpriority", "appointmentstatus",
        "reportpriority", "reportstatus",
        "studystatus", "modality", "gender", "userrole",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
