"""
Authentication service layer - pure business logic.
Handles user authentication, token generation, and token refresh.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from jose import JWTError

from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models.user import User
from app.schemas.auth import Token, TokenPayload


class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised when email or password is incorrect."""
    def __init__(self, message: str = "Invalid email or password"):
        self.message = message
        super().__init__(self.message)


class UserNotFoundError(AuthenticationError):
    """Raised when user does not exist."""
    def __init__(self, message: str = "User not found"):
        self.message = message
        super().__init__(self.message)


class InactiveUserError(AuthenticationError):
    """Raised when user account is inactive."""
    def __init__(self, message: str = "User account is inactive"):
        self.message = message
        super().__init__(self.message)


class InvalidTokenError(AuthenticationError):
    """Raised when token is invalid or expired."""
    def __init__(self, message: str = "Invalid or expired token"):
        self.message = message
        super().__init__(self.message)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Retrieve a user by email address.
    
    Args:
        db: Database session
        email: User's email address
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
    """
    Retrieve a user by their ID.
    
    Args:
        db: Database session
        user_id: User's UUID
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> User:
    """
    Authenticate a user by email and password.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        Authenticated User object
        
    Raises:
        UserNotFoundError: If no user with the email exists
        InvalidCredentialsError: If password doesn't match
        InactiveUserError: If user account is inactive
    """
    user = get_user_by_email(db, email)
    
    if not user:
        raise UserNotFoundError(f"No user found with email: {email}")
    
    if not verify_password(password, user.hashed_password):
        raise InvalidCredentialsError("Invalid email or password")
    
    if not user.is_active:
        raise InactiveUserError("User account is inactive")
    
    return user


def login(db: Session, email: str, password: str) -> Token:
    """
    Authenticate user and generate JWT tokens.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password
        
    Returns:
        Token object containing access_token, refresh_token, and token_type
        
    Raises:
        UserNotFoundError: If no user with the email exists
        InvalidCredentialsError: If password doesn't match
        InactiveUserError: If user account is inactive
    """
    # Authenticate the user (will raise exception if invalid)
    user = authenticate_user(db, email, password)
    
    # Prepare token payload
    token_data = {
        "sub": str(user.id),
        "company_id": str(user.company_id) if user.company_id else None,
        "is_superuser": user.is_superuser,
    }
    
    # Generate tokens
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    
    # Update last login timestamp
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )


def refresh_access_token(db: Session, refresh_token: str) -> Token:
    """
    Generate a new access token using a valid refresh token.
    
    Args:
        db: Database session
        refresh_token: JWT refresh token
        
    Returns:
        Token object with new access_token and same refresh_token
        
    Raises:
        InvalidTokenError: If refresh token is invalid, expired, or wrong type
        UserNotFoundError: If user from token no longer exists
        InactiveUserError: If user account is inactive
    """
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise InvalidTokenError("Invalid or expired refresh token")
    
    # Verify it's a refresh token, not an access token
    token_type = payload.get("type")
    if token_type != "refresh":
        raise InvalidTokenError("Invalid token type - expected refresh token")
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise InvalidTokenError("Invalid token payload")
    
    # Verify user still exists and is active
    user = get_user_by_id(db, UUID(user_id))
    if not user:
        raise UserNotFoundError("User no longer exists")
    
    if not user.is_active:
        raise InactiveUserError("User account is inactive")
    
    # Generate new access token with fresh data
    token_data = {
        "sub": str(user.id),
        "company_id": str(user.company_id) if user.company_id else None,
        "is_superuser": user.is_superuser,
    }
    
    new_access_token = create_access_token(data=token_data)
    
    return Token(
        access_token=new_access_token,
        refresh_token=refresh_token,  # Return the same refresh token
        token_type="bearer"
    )


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    company_id: Optional[UUID] = None,
    is_superuser: bool = False
) -> User:
    """
    Create a new user account.
    
    Args:
        db: Database session
        email: User's email address
        password: Plain text password (will be hashed)
        full_name: User's full name
        company_id: Company UUID (required for regular users)
        is_superuser: Whether user is a superuser
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If email already exists
    """
    # Check if user already exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")
    
    # Create new user
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        company_id=company_id,
        is_superuser=is_superuser,
        is_active=True,
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user
