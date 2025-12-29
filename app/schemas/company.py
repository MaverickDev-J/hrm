"""
Company schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class CompanyBase(BaseModel):
    """Base schema with common company fields."""
    name: str = Field(..., min_length=2, max_length=255, description="Company name")
    subdomain: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$",
        description="Unique subdomain (lowercase alphanumeric with hyphens)"
    )


class CompanyCreate(CompanyBase):
    """Schema for creating a new company (tenant)."""
    pass


class CompanyUpdate(BaseModel):
    """Schema for updating company details."""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    subdomain: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=100, 
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$"
    )
    is_active: Optional[bool] = None


class CompanyResponse(CompanyBase):
    """Schema for company responses."""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompanyInDB(CompanyResponse):
    """Full company data as stored in database."""
    pass
