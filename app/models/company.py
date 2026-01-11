import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy import Boolean, String, DateTime, Text
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
    
    # Business Details
    registered_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pincode: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Bank Details
    bank_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_holder_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)
    bank_pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Branding
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    signature_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    stamp_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

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

    clients: Mapped[list["Client"]] = relationship(
        "Client",
        back_populates="company",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, subdomain={self.subdomain})>"