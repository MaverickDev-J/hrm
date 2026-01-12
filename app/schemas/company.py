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
    tagline: Optional[str] = Field(None, max_length=255)
    subdomain: Optional[str] = Field(
        None, 
        min_length=2, 
        max_length=100, 
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$"
    )
    is_active: Optional[bool] = None
    
    # Business Details
    registered_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = Field(None, pattern=r'^\d{6}$')
    pan_number: Optional[str] = Field(None, pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')
    
    # Bank Details
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = Field(None, pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$')
    bank_pan: Optional[str] = Field(None, pattern=r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')

    # Branding
    logo_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    signature_url: Optional[str] = None
    stamp_url: Optional[str] = None


class CompanyResponse(CompanyBase):
    """Schema for company responses."""
    id: UUID
    is_active: bool
    tagline: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Business Details
    registered_address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    pan_number: Optional[str] = None
    
    # Bank Details
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    bank_pan: Optional[str] = None
    
    # Branding
    logo_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    signature_url: Optional[str] = None
    stamp_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CompanyProfileStatus(BaseModel):
    """Schema for company profile completeness status."""
    is_complete: bool
    missing_required_fields: list[str]
    missing_optional_fields: list[str]


class CompanyInDB(CompanyResponse):
    """Full company data as stored in database."""
    pass
