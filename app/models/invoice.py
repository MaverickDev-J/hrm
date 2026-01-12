import uuid
from datetime import date, datetime
from typing import Dict, Any, List

from sqlalchemy import String, Date, DateTime, ForeignKey, Numeric, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class Invoice(Base):
    """
    Invoice model representing a generated document.
    CRITICAL: Stores MANUAL totals input by admin, not calculated values.
    This ensures the DB record matches the generated PDF exactly, even if
    partial billing occurred.
    """
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )

    invoice_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Tenant & Client Links
    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Snapshot of who was billed
    candidate_ids: Mapped[List[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list
    )

    # Manual Financials (Store exactly what Admin typed)
    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    
    # Tax Breakdown (explicitly stored)
    cgst_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00)
    sgst_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00)
    igst_amount: Mapped[float] = mapped_column(Numeric(15, 2), default=0.00)
    
    grand_total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    # Generated Artifact
    file_url: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="GENERATED") # DRAFT, GENERATED, SENT

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
    company = relationship("Company", backref="invoices")
    client = relationship("Client", backref="invoices")

    def __repr__(self) -> str:
        return f"<Invoice(number={self.invoice_number}, total={self.grand_total})>"
