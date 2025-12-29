from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth_service import create_user as auth_create_user
from app.services.auth_service import get_user_by_id as auth_get_user_by_id


class UserServiceError(Exception):
    """Base exception for user service errors."""
    pass


class UserNotFoundError(UserServiceError):
    """Raised when user is not found."""
    pass


class AccessDeniedError(UserServiceError):
    """Raised when user permissions are insufficient."""
    pass


def assign_role_to_user(db: Session, user: User, role_name: str) -> Role:
    """
    Assign a role to a user. Creates the role if it doesn't exist for the company.
    """
    # Check if role exists for this company
    role = db.query(Role).filter(
        Role.name == role_name,
        Role.company_id == user.company_id
    ).first()

    if not role:
        # Create role if it doesn't exist
        role = Role(
            name=role_name,
            company_id=user.company_id,
            permissions={}  # Default empty permissions
        )
        db.add(role)
        db.commit()
        db.refresh(role)

    # Assign role to user if not already assigned
    if role not in user.roles:
        user.roles.append(role)
        db.commit()
        db.refresh(user)

    return role


def create_company_admin(
    db: Session, 
    company_id: UUID, 
    user_in: UserCreate, 
    current_user: User
) -> User:
    """
    Create a company admin user. Only superusers can perform this.
    """
    if not current_user.is_superuser:
        raise AccessDeniedError("Only superusers can create company admins")

    # Create the user using auth service (handles hashing and duplicates)
    # Note: user_in.company_id is ignored/overwritten by the explicit company_id arg
    user = auth_create_user(
        db=db,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        company_id=company_id,
        is_superuser=False
    )

    # Assign 'company_admin' role
    assign_role_to_user(db, user, "company_admin")
    
    return user


def create_employee(
    db: Session, 
    user_in: UserCreate, 
    current_user: User
) -> User:
    """
    Create an employee within the current user's company.
    """
    # Ensure current user belongs to a company
    if not current_user.company_id:
        raise AccessDeniedError("Superusers must use create_company_admin to create users")

    # Verify current user is an admin of this company
    # (Simple check: has 'company_admin' role or similar)
    # For now, we assume the caller ensures this check via dependency injection 
    # (e.g. get_current_company_admin), but we can double check here.
    
    # Create user in the same company
    user = auth_create_user(
        db=db,
        email=user_in.email,
        password=user_in.password,
        full_name=user_in.full_name,
        company_id=current_user.company_id,
        is_superuser=False
    )

    # Assign 'employee' role
    assign_role_to_user(db, user, "employee")

    return user


def get_users(
    db: Session, 
    current_user: User, 
    skip: int = 0, 
    limit: int = 100
) -> List[User]:
    """
    Get users with tenant isolation logic.
    - Superuser: All users
    - Company Admin: Users in their company
    - Employee: Only themselves
    """
    query = db.query(User)

    if current_user.is_superuser:
        # Superuser sees all
        pass
    
    elif current_user.company_id:
        # Check if user has admin role
        is_admin = any(r.name == 'company_admin' for r in current_user.roles)
        
        if is_admin:
            # Company admin sees all users in their company
            query = query.filter(User.company_id == current_user.company_id)
        else:
            # Regular employee sees only themselves
            query = query.filter(User.id == current_user.id)
            
    else:
        # Fallback for unconnected users (shouldn't happen for normal users)
        query = query.filter(User.id == current_user.id)

    return query.offset(skip).limit(limit).all()


def get_user_by_id(
    db: Session, 
    user_id: UUID, 
    current_user: User
) -> Optional[User]:
    """
    Get a specific user by ID, enforcing tenant isolation.
    """
    user = auth_get_user_by_id(db, user_id)
    
    if not user:
        return None

    # Access Control
    if current_user.is_superuser:
        return user
    
    if user.company_id == current_user.company_id:
        return user
        
    # Block access if trying to view user from another company
    raise AccessDeniedError("Access to this user is forbidden")


def update_user(
    db: Session,
    user_id: UUID,
    user_in: UserUpdate,
    current_user: User
) -> User:
    """
    Update a user.
    """
    user = get_user_by_id(db, user_id, current_user)
    if not user:
        raise UserNotFoundError("User not found")

    # Update fields
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.full_name is not None:
        user.full_name = user_in.full_name
    # Password update would require hashing, skipping for brevity or add if needed
    # is_active update logic, etc.

    db.commit()
    db.refresh(user)
    return user
