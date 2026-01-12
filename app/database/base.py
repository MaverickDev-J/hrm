from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    All models will inherit from this class.
    """
    pass

# Import all models here to ensure they are registered with Base.metadata
# This is crucial for Alembic autogeneration
from app.models.user import User  # noqa
from app.models.company import Company  # noqa
from app.models.role import Role  # noqa
from app.models.client import Client  # noqa
from app.models.client_column_config import ClientColumnConfig  # noqa
from app.models.candidate import Candidate  # noqa
from app.models.invoice import Invoice  # noqa