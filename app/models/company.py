import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Company(Base):
    """
    Company model representing a tenant in the multi-tenant system.
    Each company is isolated from others.
    """
    __tablename__ = "companies"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Company Details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique subdomain for tenant identification (e.g., 'acme' for acme.app. com)"
    )
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, subdomain={self.subdomain})>"