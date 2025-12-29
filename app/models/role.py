import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Role(Base):
    """
    Role model for defining user permissions within a company.
    Supports both global roles (superuser) and tenant-specific roles. 
    """
    __tablename__ = "roles"
    
    # Primary Key
    id:  Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Role Details
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Role name (e.g., 'admin', 'employee', 'manager')"
    )
    
    # Tenant Isolation
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="NULL for global roles (superuser), set for tenant-specific roles"
    )
    
    # Permissions stored as JSON
    permissions: Mapped[Optional[dict]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
        comment="Flexible permission structure, e.g., {'can_manage_users': true}"
    )
    
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
    company: Mapped[Optional["Company"]] = relationship(
        "Company",
        back_populates="roles"
    )
    
    users: Mapped[list["User"]] = relationship(
        "User",
        secondary="user_roles",
        back_populates="roles"
    )
    
    def __repr__(self) -> str:
        return f"<Role(id={self. id}, name={self.name}, company_id={self.company_id})>"