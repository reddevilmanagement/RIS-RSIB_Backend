"""
Model registry for Alembic autogenerate.
"""

from app.models.user import User
from app.models.patient import Patient
from app.models.appointment import Appointment
from app.models.study import Study
from app.models.report import Report

__all__ = [
    "User",
    "Patient",
    "Appointment",
    "Study",
    "Report",
]
