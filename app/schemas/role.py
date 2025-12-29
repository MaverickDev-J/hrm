"""
Role schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RoleBase(BaseModel):
    """Base schema with common role fields."""
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Role name (e.g., 'admin', 'employee', 'manager')"
    )
    permissions: Optional[dict] = Field(
        default_factory=dict,
        description="Role permissions as JSON object"
    )


class RoleCreate(RoleBase):
    """Schema for creating a new role within a company."""
    company_id: Optional[UUID] = Field(
        None, 
        description="Company ID (null for global roles)"
    )


class RoleUpdate(BaseModel):
    """Schema for updating role details."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    permissions: Optional[dict] = None


class RoleResponse(RoleBase):
    """Schema for role responses."""
    id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoleWithPermissions(RoleResponse):
    """Role with expanded permissions for authorization checks."""
    pass


class RoleInDB(RoleResponse):
    """Full role data as stored in database."""
    pass
