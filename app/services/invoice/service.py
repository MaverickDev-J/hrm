from datetime import date
from uuid import UUID
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from app.models.invoice import Invoice
from app.schemas.invoice import ManualTotals

# Import from sibling modules
from .generator import InvoiceGenerator
from .files import cleanup_invoice_file



def generate_invoice(
    db: Session,
    company_id: UUID, 
    client_id: UUID, 
    candidate_ids: List[UUID], 
    manual_totals: ManualTotals,
    invoice_number: str,
    invoice_date: date,
    status: str = "DRAFT"
) -> Invoice:
    # 0. Validation
    # Check Invoice Number Uniqueness for this Company
    existing = db.query(Invoice).filter(
        Invoice.company_id == company_id,
        Invoice.invoice_number == invoice_number
    ).first()
    if existing:
        raise ValueError(f"Invoice number '{invoice_number}' already exists.")

    generator = InvoiceGenerator(db)
    
    # 1. Aggregate
    data = generator.prepare_invoice_data(
        company_id, client_id, candidate_ids, manual_totals, invoice_number, invoice_date
    )
    
    # 2. Generate
    file_url = generator.generate_docx(data)
    
    # 3. Save Record
    db_invoice = Invoice(
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        company_id=company_id,
        client_id=client_id,
        candidate_ids=[str(cid) for cid in candidate_ids],
        
        # Store Immutable Snapshot
        invoice_snapshot=data,
        
        # Financials
        subtotal=manual_totals.subtotal,
        cgst_rate=manual_totals.cgst_rate,
        cgst_amount=manual_totals.cgst_amount,
        sgst_rate=manual_totals.sgst_rate,
        sgst_amount=manual_totals.sgst_amount,
        igst_rate=manual_totals.igst_rate,
        igst_amount=manual_totals.igst_amount,
        grand_total=manual_totals.grand_total,
        
        file_url=file_url,
        status=status
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

def send_invoice(db: Session, invoice: Invoice) -> Invoice:
    """
    Mark invoice as SENT.
    """
    if invoice.status != "GENERATED":
        # Theoretically you might allow sending DRAFT which auto-finalizes,
        # but to keep it strict: must be GENERATED first.
        # Or maybe re-sending is allowed? 
        # Requirement: DRAFT -> GENERATED -> SENT.
        if invoice.status == "SENT":
            return invoice # Idempotent
        raise ValueError("Only GENERATED invoices can be marked as SENT. Finalize the draft first.")
        
    invoice.status = "SENT"
    db.commit()
    db.refresh(invoice)
    return invoice

def update_invoice(
    db: Session,
    invoice: Invoice,
    candidate_ids: Optional[List[UUID]] = None,
    manual_totals: Optional[ManualTotals] = None,
    invoice_date: Optional[date] = None,
    invoice_number: Optional[str] = None
) -> Invoice:
    """
    Update a DRAFT invoice. Regenerates DOCX and Snapshot.
    """
    if invoice.status != "DRAFT":
        raise ValueError("Only DRAFT invoices can be edited.")
        
    # Validation: Unique Invoice Number (if changing)
    if invoice_number and invoice_number != invoice.invoice_number:
        existing = db.query(Invoice).filter(
            Invoice.company_id == invoice.company_id,
            Invoice.invoice_number == invoice_number
        ).first()
        if existing:
            raise ValueError(f"Invoice number '{invoice_number}' already exists.")
            
    # File Cleanup: Delete old DOCX
    if invoice.file_url:
        cleanup_invoice_file(invoice.file_url)

    # Prepare new data
    # Use provided values or fallback to existing
    # Note: candidate_ids in DB is list of strings, input is list of UUIDs
    
    final_candidate_ids = candidate_ids if candidate_ids is not None else [UUID(cid) for cid in invoice.candidate_ids]
    
    final_invoice_number = invoice_number if invoice_number else invoice.invoice_number
    final_invoice_date = invoice_date if invoice_date else invoice.invoice_date
    
    # Reconstruct manual_totals if not provided (from DB columns)
    if manual_totals:
        final_manual_totals = manual_totals
    else:
        final_manual_totals = ManualTotals(
            subtotal=invoice.subtotal,
            cgst_rate=invoice.cgst_rate or 0.0,
            cgst_amount=invoice.cgst_amount,
            sgst_rate=invoice.sgst_rate or 0.0,
            sgst_amount=invoice.sgst_amount,
            igst_rate=invoice.igst_rate or 0.0,
            igst_amount=invoice.igst_amount,
            grand_total=invoice.grand_total
        )

    # Regenerate Data & File
    generator = InvoiceGenerator(db)
    data = generator.prepare_invoice_data(
        company_id=invoice.company_id,
        client_id=invoice.client_id,
        candidate_ids=final_candidate_ids,
        manual_totals=final_manual_totals,
        invoice_number=final_invoice_number,
        invoice_date=final_invoice_date
    )
    
    file_url = generator.generate_docx(data)
    
    # Update DB Record
    invoice.invoice_number = final_invoice_number
    invoice.invoice_date = final_invoice_date
    invoice.candidate_ids = [str(cid) for cid in final_candidate_ids]
    invoice.invoice_snapshot = data
    invoice.file_url = file_url
    
    # Update Financials
    invoice.subtotal = final_manual_totals.subtotal
    invoice.cgst_rate = final_manual_totals.cgst_rate
    invoice.cgst_amount = final_manual_totals.cgst_amount
    invoice.sgst_rate = final_manual_totals.sgst_rate
    invoice.sgst_amount = final_manual_totals.sgst_amount
    invoice.igst_rate = final_manual_totals.igst_rate
    invoice.igst_amount = final_manual_totals.igst_amount
    invoice.grand_total = final_manual_totals.grand_total
    
    db.commit()
    db.refresh(invoice)
    return invoice

def finalize_invoice(db: Session, invoice: Invoice) -> Invoice:
    """
    Transition invoice from DRAFT to GENERATED.
    Freezes the snapshot state.
    """
    if invoice.status != "DRAFT":
        raise ValueError("Only DRAFT invoices can be finalized.")
        
    invoice.status = "GENERATED"
    db.commit()
    db.refresh(invoice)
    return invoice

def preview_draft_invoice(
    db: Session,
    company_id: UUID, 
    client_id: UUID, 
    candidate_ids: List[UUID], 
    manual_totals: ManualTotals,
    invoice_number: str,
    invoice_date: date
) -> Dict[str, Any]:
    """
    Generate a preview of the invoice without saving to DB.
    Returns the data dictionary which includes the file_url (if we generated a temp file).
    """
    generator = InvoiceGenerator(db)
    
    # 1. Aggregate
    data = generator.prepare_invoice_data(
        company_id, client_id, candidate_ids, manual_totals, invoice_number, invoice_date
    )
    
    # 2. Generate Temp File
    # We use the same generation logic. The file will be created.
    # Ideally we'd map this to a temp location, but for simplicity/access we use the same dir.
    # It won't be tracked in DB, so it's "orphaned" until cleaned up or overwritten.
    file_url = generator.generate_docx(data)
    
    # Return data + file_url for frontend preview
    # We'll attach file_url to the data dict for convenience response
    response_data = data.copy()
    response_data["file_url"] = file_url
    
    return response_data

def delete_draft_invoice(db: Session, invoice: Invoice):
    """
    Delete a DRAFT invoice and its associated file.
    """
    if invoice.status != "DRAFT":
        raise ValueError("Only DRAFT invoices can be deleted.")
        
    # File Cleanup
    if invoice.file_url:
        cleanup_invoice_file(invoice.file_url)

    db.delete(invoice)
    db.commit()

def get_latest_invoice_data_by_client_id(db: Session, client_id: UUID, company_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Retrieve data for the LATEST invoice generated for a specific client.
    Prefer returning the stored immutable snapshot.
    """
    # Fix: Filter by company_id for multitenant security
    invoice = db.query(Invoice).filter(
        Invoice.client_id == client_id,
        Invoice.company_id == company_id
    ).order_by(Invoice.invoice_date.desc(), Invoice.id.desc()).first()
    
    if not invoice:
        return None

    # 1. Prefer Snapshot (Fast & Immutable)
    if invoice.invoice_snapshot:
        return invoice.invoice_snapshot
        
    # 2. Fallback: Reconstruct from live tables (Legacy support)
    # This is dangerous if data changed, but necessary for old records
    manual_totals = ManualTotals(
        subtotal=invoice.subtotal,
        cgst_rate=invoice.cgst_rate if hasattr(invoice, 'cgst_rate') else 0.0,
        cgst_amount=invoice.cgst_amount,
        sgst_rate=invoice.sgst_rate if hasattr(invoice, 'sgst_rate') else 0.0,
        sgst_amount=invoice.sgst_amount,
        igst_rate=invoice.igst_rate if hasattr(invoice, 'igst_rate') else 0.0,
        igst_amount=invoice.igst_amount,
        grand_total=invoice.grand_total
    )
    
    if invoice.candidate_ids is None:
        candidate_uuids = []
    else:
        if isinstance(invoice.candidate_ids, list):
             candidate_uuids = [UUID(str(cid)) for cid in invoice.candidate_ids]
        elif isinstance(invoice.candidate_ids, str):
             candidate_uuids = [] 
        else:
             candidate_uuids = []

    generator = InvoiceGenerator(db)
    data = generator.prepare_invoice_data(
        company_id=invoice.company_id,
        client_id=invoice.client_id,
        candidate_ids=candidate_uuids,
        manual_totals=manual_totals,
        invoice_number=invoice.invoice_number,
        invoice_date=invoice.invoice_date
    )
    
    return data