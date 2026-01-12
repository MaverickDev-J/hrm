from typing import List, Optional, Dict
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
