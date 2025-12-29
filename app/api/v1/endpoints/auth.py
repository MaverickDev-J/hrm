"""
Authentication API endpoints.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.schemas.auth import Token, RefreshRequest, LoginRequest
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import (
    login,
    refresh_access_token,
    create_user,
    AuthenticationError,
    InvalidCredentialsError,
    UserNotFoundError,
    InactiveUserError,
    InvalidTokenError,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password",
    description="Authenticate user and return JWT access and refresh tokens."
)
async def login_endpoint(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)]
) -> Token:
    """
    OAuth2 compatible login endpoint.
    
    - **username**: User's email address
    - **password**: User's password
    
    Returns JWT tokens on successful authentication.
    """
    try:
        return login(db, email=form_data.username, password=form_data.password)
    except (InvalidCredentialsError, UserNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )


@router.post(
    "/login/json",
    response_model=Token,
    summary="Login with JSON body",
    description="Alternative login endpoint accepting JSON body instead of form data."
)
async def login_json_endpoint(
    credentials: LoginRequest,
    db: Annotated[Session, Depends(get_db)]
) -> Token:
    """
    Login endpoint accepting JSON body.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT tokens on successful authentication.
    """
    try:
        return login(db, email=credentials.email, password=credentials.password)
    except (InvalidCredentialsError, UserNotFoundError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token",
    description="Get a new access token using a valid refresh token."
)
async def refresh_token_endpoint(
    request: RefreshRequest,
    db: Annotated[Session, Depends(get_db)]
) -> Token:
    """
    Refresh the access token.
    
    - **refresh_token**: Valid JWT refresh token
    
    Returns new access token with the same refresh token.
    """
    try:
        return refresh_access_token(db, refresh_token=request.refresh_token)
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (UserNotFoundError, InactiveUserError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new superuser (dev only)",
    description="Create a new superuser account. For development/testing only."
)
async def register_superuser(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)]
) -> UserResponse:
    """
    Register a new superuser account.
    
    Note: In production, this endpoint should be protected or removed.
    This is provided for initial setup and testing.
    """
    try:
        # Force superuser creation for this endpoint
        user = create_user(
            db=db,
            email=user_data.email,
            password=user_data.password,
            full_name=user_data.full_name,
            company_id=user_data.company_id,
            is_superuser=user_data.is_superuser,
        )
        return UserResponse.model_validate(user)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Retrieve the currently authenticated user."
)
async def read_users_me(
    current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserResponse:
    """
    Get current user.
    """
    return current_user
