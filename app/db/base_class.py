"""
Base SQLAlchemy class.
All ORM models should inherit from this Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
