from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ClientBase(BaseModel):
    """Base schema with common client fields."""
    client_name: str = Field(..., min_length=2, max_length=255)
    client_address: str = Field(..., min_length=10)
    city: str
    state: str
    pincode: str = Field(..., pattern=r'^\d{6}$')
    gstin: str = Field(..., pattern=r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$')
    pan_number: str = Field(..., pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')


class ClientCreate(ClientBase):
    """Schema for creating a new client."""
    pass


class ClientUpdate(BaseModel):
    """Schema for updating client details."""
    client_name: Optional[str] = Field(None, min_length=2, max_length=255)
    client_address: Optional[str] = Field(None, min_length=10)
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    gstin: Optional[str] = Field(None, pattern=r'^\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}$')
    pan_number: Optional[str] = Field(None, pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    """Schema for client responses."""
    id: UUID
    company_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ClientListResponse(BaseModel):
    """Schema for paginated client list."""
    clients: list[ClientResponse]
    total: int
    page: int
    limit: int
