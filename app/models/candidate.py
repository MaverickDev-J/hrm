import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class Candidate(Base):
    """
    Candidate model representing a person placed at a client site.
    Stores dynamic data in JSONB, including the CRITICAL 'amount' field
    which is manually entered by the admin.
    """
    __tablename__ = "candidates"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    # Tenant Isolation
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Client Association
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Dynamic Data + Fixed Amount
    # Must contain key "amount" (numeric)
    candidate_data: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {}
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

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
    company = relationship("Company", backref="candidates")
    client = relationship("Client", backref="candidates")

    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, client_id={self.client_id}, company_id={self.company_id})>"
