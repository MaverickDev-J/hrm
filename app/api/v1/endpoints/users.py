from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import (
    get_current_user,
    get_current_active_superuser,
    get_current_company_admin
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import (
    create_company_admin,
    create_employee,
    get_users,
    get_user_by_id,
    update_user,
    AccessDeniedError,
    UserNotFoundError
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "/admin",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Company Admin",
    description="Create a new company admin. Only superusers can do this."
)
async def create_company_admin_endpoint(
    company_id: UUID,
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """Create a company admin (Superuser only)."""
    try:
        return create_company_admin(db, company_id, user_in, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/employee",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Employee",
    description="Create a new employee in the current user's company. Only company admins can do this."
)
async def create_employee_endpoint(
    user_in: UserCreate,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """Create an employee (Company Admin only)."""
    try:
        return create_employee(db, user_in, current_user)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/",
    response_model=List[UserResponse],
    summary="List Users",
    description="List users. Superusers see all. Admins see company users. Employees see themselves."
)
async def read_users(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 100
) -> List[UserResponse]:
    """List users based on role and tenant."""
    return get_users(db, current_user, skip, limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID",
    description="Get user details. Subject to tenant isolation."
)
async def read_user(
    user_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """Get specific user."""
    try:
        user = get_user_by_id(db, user_id, current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except AccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    description="Update user details."
)
async def update_user_endpoint(
    user_id: UUID,
    user_in: UserUpdate,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """Update user (Admin only)."""
    try:
        return update_user(db, user_id, user_in, current_user)
    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    except AccessDeniedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
