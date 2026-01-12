from typing import List, Optional, Dict, Any
import uuid
from datetime import date, datetime
from pydantic import BaseModel, Field

# --- Manual Totals Schema ---
class ManualTotals(BaseModel):
    subtotal: float = Field(..., description="Manually entered subtotal")
    cgst_amount: float = Field(0.0, description="CGST Amount")
    sgst_amount: float = Field(0.0, description="SGST Amount")
    igst_amount: float = Field(0.0, description="IGST Amount")
    grand_total: float = Field(..., description="Manually entered Grand Total")

# --- Generation Request ---
class InvoiceGenerateRequest(BaseModel):
    client_id: uuid.UUID
    candidate_ids: List[uuid.UUID]
    invoice_number: str
    invoice_date: date
    manual_totals: ManualTotals

# --- Response ---
class InvoiceResponse(BaseModel):
    id: uuid.UUID
    invoice_number: str
    file_url: str
    grand_total: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

# --- Detailed Data Response Schemas ---

class InvoiceCompanyDetail(BaseModel):
    name: str
    tagline: Optional[str] = None
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    pan: Optional[str] = None
    banner_url: Optional[str] = None
    stamp_url: Optional[str] = None
    signature_url: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None

class InvoiceClientDetail(BaseModel):
    name: str
    address: str
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gstin: str
    pan: Optional[str] = None

class InvoiceColumnDef(BaseModel):
    field_name: str
    display_label: str
    width: float

class InvoiceLineItem(BaseModel):
    serial_no: int
    amount: float
    # Allow extra dynamic fields from config
    class Config:
        extra = "allow" 

class InvoiceDataResponse(BaseModel):
    invoice_number: str
    invoice_date: str
    company: InvoiceCompanyDetail
    client: InvoiceClientDetail
    columns: List[InvoiceColumnDef]
    line_items: List[Dict[str, Any]] # Using Dict to support dynamic columns easily
    financials: ManualTotals
