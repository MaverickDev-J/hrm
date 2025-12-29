"""
FastAPI dependencies for authentication and authorization.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import TokenPayload

# OAuth2 scheme - expects token in Authorization header as "Bearer <token>"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        token: JWT access token from Authorization header
        db: Database session
        
    Returns:
        User object if token is valid
        
    Raises:
        HTTPException 401: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None:
            raise credentials_exception
        
        # Ensure this is an access token, not a refresh token
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_superuser(
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    """
    Dependency to get the current user and verify they are a superuser.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        User object if user is a superuser
        
    Raises:
        HTTPException 403: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return current_user


async def get_current_company_admin(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)]
) -> User:
    """
    Dependency to get the current user and verify they are a company admin.
    Company admins can manage users within their own company.
    
    Args:
        current_user: The authenticated user
        db: Database session
        
    Returns:
        User object if user is a company admin or superuser
        
    Raises:
        HTTPException 403: If user doesn't have admin privileges
    """
    # Superusers can access everything
    if current_user.is_superuser:
        return current_user
    
    # Check if user has admin role within their company
    if not current_user.company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with any company"
        )
    
    # Check for admin role in user's roles
    has_admin_role = any(
        role.name.lower() in ["admin", "company_admin", "hr_admin"]
        for role in current_user.roles
    )
    
    if not has_admin_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


def get_company_id_from_user(user: User) -> Optional[UUID]:
    """
    Helper function to extract company_id from user.
    Superusers may have None as company_id.
    
    Args:
        user: User object
        
    Returns:
        Company UUID or None for superusers
    """
    return user.company_id


# Type aliases for cleaner dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentSuperuser = Annotated[User, Depends(get_current_active_superuser)]
CurrentCompanyAdmin = Annotated[User, Depends(get_current_company_admin)]
DbSession = Annotated[Session, Depends(get_db)]
