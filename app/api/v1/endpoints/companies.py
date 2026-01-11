from typing import List, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_active_superuser, get_current_company_admin
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate, CompanyProfileStatus
from app.services.company_service import (
    create_company,
    get_all_companies,
    get_company_by_id,
    update_company,
    check_profile_completeness,
    SubdomainAlreadyExistsError,
    CompanyNotFoundError,
)
from app.utils.files import save_upload_file

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


@router.patch(
    "/{company_id}",
    response_model=CompanyResponse,
    summary="Update company profile",
    description="Update company details. Company Admin can only update their own company."
)
async def update_company_details(
    company_id: UUID,
    company_in: CompanyUpdate,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> CompanyResponse:
    """
    Update company details (Company Admin or Superuser).
    """
    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
        
    # Permission Check
    if not current_user.is_superuser:
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this company"
            )
            
    try:
        return update_company(db, company, company_in)
    except SubdomainAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e.message)
        )


@router.post(
    "/{company_id}/upload/{image_type}",
    response_model=dict,
    summary="Upload company branding image",
    description="Upload logo, banner, signature, or stamp."
)
async def upload_company_image(
    company_id: UUID,
    image_type: str,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)],
    file: UploadFile = File(...)
) -> dict:
    """
    Upload company image (Company Admin or Superuser).
    """
    allowed_types = ["logo", "banner", "signature", "stamp"]
    if image_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type. Allowed: {', '.join(allowed_types)}"
        )
        
    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )

    # Permission Check
    if not current_user.is_superuser:
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this company"
            )

    # Save file
    url = await save_upload_file(file, company_id, image_type)
    
    # Update company record
    # Map image_type to field name
    field_map = {
        "logo": "logo_url",
        "banner": "banner_image_url",
        "signature": "signature_url",
        "stamp": "stamp_url"
    }
    
    update_data = CompanyUpdate(**{field_map[image_type]: url})
    update_company(db, company, update_data)
    
    return {"url": url}


@router.get(
    "/{company_id}/profile-status",
    response_model=CompanyProfileStatus,
    summary="Check profile completeness",
    description="Check which fields are missing from company profile."
)
async def get_profile_status(
    company_id: UUID,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
) -> CompanyProfileStatus:
    """
    Check profile status (Company Admin or Superuser).
    """
    company = get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
        
    # Permission Check
    if not current_user.is_superuser:
        if current_user.company_id != company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this company"
            )
            
    return check_profile_completeness(company)
