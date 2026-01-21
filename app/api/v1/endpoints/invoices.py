from datetime import date
from typing import Annotated, Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_company_admin
from app.models.user import User
from app.models.client import Client
from app.models.candidate import Candidate
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceGenerateRequest, InvoiceResponse, InvoiceDataResponse, InvoiceUpdate, InvoicePreviewResponse
from app.services.invoice_service import generate_invoice, update_invoice, finalize_invoice, preview_draft_invoice, delete_draft_invoice, send_invoice

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.get(
    "/",
    response_model=List[InvoiceResponse],
    summary="List Invoices",
    description="List invoices with filtering and pagination."
)
async def list_invoices(
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)],
    status: Optional[str] = Query(None, description="Filter by status (DRAFT, GENERATED, SENT)"),
    client_id: Optional[UUID] = Query(None, description="Filter by Client ID"),
    from_date: Optional[date] = Query(None, description="Filter by invoice date >= from_date"),
    to_date: Optional[date] = Query(None, description="Filter by invoice date <= to_date"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page")
):
    """
    List invoices belonging to the current user's company.
    """
    query = db.query(Invoice).filter(Invoice.company_id == current_user.company_id)
    
    if status:
        query = query.filter(Invoice.status == status)
    if client_id:
        query = query.filter(Invoice.client_id == client_id)
    if from_date:
        query = query.filter(Invoice.invoice_date >= from_date)
    if to_date:
        query = query.filter(Invoice.invoice_date <= to_date)
        
    # Pagination
    offset = (page - 1) * page_size
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(page_size).all()
    
    return invoices

@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get Invoice Detail",
    description="Retrieve details of a specific invoice."
)
async def get_invoice(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Get a single invoice by ID.
    Enforces tenant isolation.
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if not current_user.is_superuser:
        if invoice.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Invoice not found")
             
    return invoice

@router.post(
    "/preview-draft",
    response_model=InvoicePreviewResponse,
    summary="Preview Draft Invoice",
    description="Generate a temporary invoice preview without saving to the database."
)
async def preview_draft(
    request: InvoiceGenerateRequest,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Preview invoice generation.
    """
    # 1. Validate Client Access
    client = db.query(Client).filter(Client.id == request.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    if not current_user.is_superuser:
        if client.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Client not found")
        company_id = current_user.company_id
    else:
        company_id = client.company_id

    # 2. Validate Candidates
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

    # 3. Generate Preview
    try:
        data = preview_draft_invoice(
            db,
            company_id=company_id,
            client_id=request.client_id,
            candidate_ids=request.candidate_ids,
            manual_totals=request.manual_totals,
            invoice_number=request.invoice_number,
            invoice_date=request.invoice_date
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return data

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
        invoice_date=request.invoice_date,
        status=request.status
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
        
    data = get_latest_invoice_data_by_client_id(db, client_id, client.company_id)
    return data

@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Update Draft Invoice",
    description="Update an existing invoice. Only allowed if status is DRAFT."
)
async def update_draft_invoice(
    invoice_id: UUID,
    request: InvoiceUpdate,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Update details of a DRAFT invoice.
    Regenerates the DOCX file and snapshot.
    """
    # 1. Fetch Invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # 2. Security Check (Tenant & Ownership)
    if not current_user.is_superuser:
        if invoice.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 3. Status Check
    if invoice.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only DRAFT invoices can be edited."
        )
        
    # 4. Update
    try:
        updated_invoice = update_invoice(
            db,
            invoice,
            candidate_ids=request.candidate_ids,
            manual_totals=request.manual_totals,
            invoice_date=request.invoice_date,
            invoice_number=request.invoice_number
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return updated_invoice

@router.post(
    "/{invoice_id}/finalize",
    response_model=InvoiceResponse,
    summary="Finalize Invoice",
    description="Transition invoice from DRAFT to GENERATED. Locks the invoice snapshot."
)
async def finalize_draft_invoice(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Finalize a DRAFT invoice.
    """
    # 1. Fetch Invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # 2. Security Check
    if not current_user.is_superuser:
        if invoice.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Invoice not found")
             
    # 3. Status Check
    if invoice.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only DRAFT invoices can be finalized."
        )
        
    # 4. Finalize
    try:
        finalized_invoice = finalize_invoice(db, invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return finalized_invoice

@router.post(
    "/{invoice_id}/send",
    response_model=InvoiceResponse,
    summary="Mark Invoice as Sent",
    description="Mark a GENERATED invoice as SENT."
)
async def send_invoice_endpoint(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Mark invoice as SENT.
    """
    # 1. Fetch Invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # 2. Security Check
    if not current_user.is_superuser:
        if invoice.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Invoice not found")
             
    # 3. Status Check
    if invoice.status != "GENERATED":
        # Allow SENT to be idempotent
        if invoice.status == "SENT":
            return invoice
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only GENERATED invoices can be marked as SENT. Finalize the draft first."
        )
        
    # 4. Send
    try:
        sent_invoice = send_invoice(db, invoice)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    return sent_invoice

@router.delete(
    "/{invoice_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Draft Invoice",
    description="Delete a DRAFT invoice. Finalized invoices cannot be deleted."
)
async def delete_draft(
    invoice_id: UUID,
    current_user: Annotated[User, Depends(get_current_company_admin)],
    db: Annotated[Session, Depends(get_db)]
):
    """
    Delete a draft invoice.
    """
    # 1. Fetch Invoice
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    # 2. Security Check
    if not current_user.is_superuser:
        if invoice.company_id != current_user.company_id:
             raise HTTPException(status_code=404, detail="Invoice not found")
             
    # 3. Status Check
    if invoice.status != "DRAFT":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Only DRAFT invoices can be deleted."
        )
        
    # 4. Delete
    delete_draft_invoice(db, invoice)
    
    return None
