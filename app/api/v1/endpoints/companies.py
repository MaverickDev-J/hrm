from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_active_superuser
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse
from app.services.company_service import (
    create_company,
    get_all_companies,
    get_company_by_id,
    SubdomainAlreadyExistsError,
    CompanyNotFoundError,
)

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.post(
    "/",
    response_model=CompanyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new company",
    description="Create a new company tenant. Only superusers can perform this action."
)
async def create_new_company(
    company_in: CompanyCreate,
    current_superuser: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[Session, Depends(get_db)]
) -> CompanyResponse:
    """
    Create a new company (superuser only).
    """
    try:
        return create_company(db, company_in)
    except SubdomainAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e.message)
        )


@router.get(
    "/",
    response_model=List[CompanyResponse],
    summary="List all companies",
    description="Retrieve a list of all companies. Only superusers can perform this action."
)
async def list_companies(
    current_superuser: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[Session, Depends(get_db)],
    skip: int = 0,
    limit: int = 100
) -> List[CompanyResponse]:
    """
    List all companies (superuser only).
    """
    return get_all_companies(db, skip=skip, limit=limit)


@router.get(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Get company by ID",
    description="Retrieve specific company details. Only superusers can perform this action."
)
async def read_company(
    company_id: UUID,
    current_superuser: Annotated[User, Depends(get_current_active_superuser)],
    db: Annotated[Session, Depends(get_db)]
) -> CompanyResponse:
    """
    Get company details by ID (superuser only).
    """
    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return company
