from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.company import CompanyCreate, CompanyUpdate


class CompanyServiceError(Exception):
    """Base exception for company service errors."""
    pass


class SubdomainAlreadyExistsError(CompanyServiceError):
    """Raised when trying to create a company with an existing subdomain."""
    def __init__(self, message: str = "Subdomain already exists"):
        self.message = message
        super().__init__(self.message)


class CompanyNotFoundError(CompanyServiceError):
    """Raised when a company is not found."""
    def __init__(self, message: str = "Company not found"):
        self.message = message
        super().__init__(self.message)


def get_company_by_subdomain(db: Session, subdomain: str) -> Optional[Company]:
    """Retrieve a company by its subdomain."""
    return db.query(Company).filter(Company.subdomain == subdomain).first()


def get_company_by_id(db: Session, company_id: UUID) -> Optional[Company]:
    """Retrieve a company by its ID."""
    return db.query(Company).filter(Company.id == company_id).first()


def get_all_companies(db: Session, skip: int = 0, limit: int = 100) -> List[Company]:
    """Retrieve all companies with pagination."""
    return db.query(Company).offset(skip).limit(limit).all()


def create_company(db: Session, company_in: CompanyCreate) -> Company:
    """
    Create a new company.
    
    Raises:
        SubdomainAlreadyExistsError: If subdomain is already taken.
    """
    # Check if subdomain exists
    if get_company_by_subdomain(db, company_in.subdomain):
        raise SubdomainAlreadyExistsError(f"Subdomain '{company_in.subdomain}' is already taken")
    
    # Create new company
    db_company = Company(
        name=company_in.name,
        subdomain=company_in.subdomain,
        is_active=True
    )
    
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return db_company
