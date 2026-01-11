import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Client(Base):
    """
    Client model representing a client of a company.
    Linked to a specific company (tenant) and isolated from others.
    """
    __tablename__ = "clients"
    
    # Primary Key
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Tenant Link
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Client Details
    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    pincode: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Tax Details
    gstin: Mapped[str] = mapped_column(String(15), nullable=False)
    pan_number: Mapped[str] = mapped_column(String(10), nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    
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
    company: Mapped["Company"] = relationship(
        "Company",
        back_populates="clients"
    )
    
    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name={self.client_name}, company_id={self.company_id})>"
