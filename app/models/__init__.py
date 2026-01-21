from app.database.base import Base
from app.models.client import Client
from app.models.company import Company
from app.models.role import Role
from app.models.user import User, user_roles
from app.models.candidate import Candidate
from app.models.invoice import Invoice

# Export all models for Alembic auto-detection
__all__ = ["Base", "Client", "Company", "Role", "User", "user_roles", "Candidate", "Invoice"]