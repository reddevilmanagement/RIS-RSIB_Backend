"""
SQLAlchemy declarative base — all models must import from here.

IMPORTANT: All models must be imported in this file so Alembic
can auto-detect them when generating migration scripts.
"""

from sqlalchemy.orm import DeclarativeBase, declared_attr


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Auto-generate table name from class name (snake_case)."""
        import re
        name = cls.__name__
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


# ─── Model registry — order matters for FK resolution ─────────────────
from app.models.user import User                  # noqa: F401, E402
from app.models.patient import Patient            # noqa: F401, E402
from app.models.appointment import Appointment    # noqa: F401, E402
from app.models.study import Study                # noqa: F401, E402
from app.models.report import Report              # noqa: F401, E402
