"""
Schemas package - exports all Pydantic schemas.
"""
from app.schemas.company import (
    CompanyBase,
    CompanyCreate,
    CompanyUpdate,
    CompanyResponse,
    CompanyInDB,
)
from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithPermissions,
    RoleInDB,
)
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserWithRoles,
)
from app.schemas.auth import (
    LoginRequest,
    Token,
    TokenPayload,
    RefreshRequest,
    PasswordChange,
    PasswordReset,
)


__all__ = [
    # Company
    "CompanyBase",
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyInDB",
    # Role
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithPermissions",
    "RoleInDB",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserWithRoles",
    # Auth
    "LoginRequest",
    "Token",
    "TokenPayload",
    "RefreshRequest",
    "PasswordChange",
    "PasswordReset",
]
