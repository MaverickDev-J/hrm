from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_company_admin
from app.models.user import User
from app.models.client import Client
from app.models.candidate import Candidate
from app.schemas.invoice import InvoiceGenerateRequest, InvoiceResponse, InvoiceDataResponse
from app.services.invoice_service import generate_invoice

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.post(
    "/generate",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Invoice",
    description="Generate a DOCX invoice with manual financial totals."
)
async def create_invoice(
    request: InvoiceGenerateRequest,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Generate an invoice for a client.
    Enforces tenant isolation.
    """
    # 1. Validate Client
    client = db.query(Client).filter(Client.id == request.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # Tenant Check
    if not current_user.is_superuser:
        if client.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Client not found")
        company_id = current_user.company_id
    else:
        # Superuser generating invoice
        # Must derive company_id from client
        company_id = client.company_id

    # 2. Validate Candidates
    # Check if all candidates exist and belong to the client/company
    # (Optional: check if already invoiced? Requirement doesn't specify check, but we usually should. 
    # For now, just valid ownership check).
    candidates = db.query(Candidate).filter(
        Candidate.id.in_(request.candidate_ids),
        Candidate.client_id == request.client_id,
        Candidate.company_id == company_id
    ).all()
    
    if len(candidates) != len(request.candidate_ids):
        raise HTTPException(
            status_code=400, 
            detail="One or more candidates not found or do not belong to this client."
        )

    # 3. Check Invoice Number Uniqueness
    # (Service might handle DB integrity error, but checking here is cleaner)
    # Actually, service is better place or DB constraint. DB has unique constraint.
    # We'll let DB integrity error happen or check. Let's rely on DB or Service.

    # 4. Generate
    invoice = generate_invoice(
        db,
        company_id=company_id,
        client_id=request.client_id,
        candidate_ids=request.candidate_ids,
        manual_totals=request.manual_totals,
        invoice_number=request.invoice_number,
        invoice_date=request.invoice_date
    )
    
    return invoice

@router.get(
    "/client/{client_id}/data",
    response_model=InvoiceDataResponse,
    summary="Get Latest Invoice Data for Client",
    description="Retrieve the complete data structure of the MOST RECENT invoice generated for the specified client."
)
async def get_client_latest_invoice_data(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get detailed data for the client's latest invoice.
    """
    from app.services.invoice_service import get_latest_invoice_data_by_client_id
    from app.models.client import Client
    
    # Check client existence and ownership
    client = db.query(Client).filter(Client.id == client_id).first()
    if not client:
         raise HTTPException(status_code=404, detail="Client not found")
         
    if not current_user.is_superuser and client.company_id != current_user.company_id:
        raise HTTPException(status_code=404, detail="Client not found") # Hide if unauthorized
        
    data = get_latest_invoice_data_by_client_id(db, client_id)
    if not data:
        raise HTTPException(status_code=404, detail="No invoices found for this client")
        
    return data
