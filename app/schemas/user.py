"""
User schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator


class UserBase(BaseModel):
    """Base schema with common user fields."""
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(
        ..., 
        min_length=8, 
        max_length=100,
        description="Password (min 8 characters)"
    )
    company_id: Optional[UUID] = Field(
        None, 
        description="Company ID (required for regular users, null for superusers)"
    )
    is_superuser: bool = Field(
        default=False, 
        description="Whether user is a system superuser"
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password has minimum complexity."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseModel):
    """Schema for updating user details."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user responses (excludes sensitive data)."""
    id: UUID
    is_active: bool
    is_superuser: bool
    company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserInDB(UserResponse):
    """User data as stored in database (includes hashed password)."""
    hashed_password: str


class UserWithRoles(UserResponse):
    """User response with associated roles."""
    roles: List["RoleBasic"] = []


class RoleBasic(BaseModel):
    """Minimal role info for embedding in user responses."""
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


# Update forward reference
UserWithRoles.model_rebuild()
