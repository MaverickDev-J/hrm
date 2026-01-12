import uuid
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

class ClientColumnConfig(Base):
    """
    Configuration for dynamic invoice columns for a specific client.
    Stores definition of fields like 'Process', 'DOJ', 'Days' etc.
    'Amount' field is logically required but configured here for display properties.
    """
    __tablename__ = "client_column_configs"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
        index=True
    )
    
    # Linked to Client (One-to-One mostly, but 1-to-many allowed by schema just in case)
    client_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"),
        nullable=False,
        unique=True, # Enforcing 1-to-1 for now as per requirements
        index=True
    )

    # The magic field: Stores list of column definitions
    # Example: { "columns": [ { "field_name": "process", "display_label": "Process", "width": "1.5"... } ] }
    column_definitions: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {"columns": []}
    )

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
    client = relationship("Client", backref="column_config")

    def __repr__(self) -> str:
        return f"<ClientColumnConfig(id={self.id}, client_id={self.client_id})>"
