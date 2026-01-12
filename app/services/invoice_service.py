import os
from datetime import datetime, date
from uuid import UUID
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

from app.models.invoice import Invoice
from app.models.client import Client
from app.models.company import Company
from app.models.candidate import Candidate
from app.services.client_service import get_client_column_config
from app.schemas.invoice import ManualTotals

# Paths
STATIC_DIR = "static"
INVOICE_DIR = os.path.join(STATIC_DIR, "invoices")
os.makedirs(INVOICE_DIR, exist_ok=True)

class InvoiceGenerator:
    def __init__(self, db: Session):
        self.db = db

    def prepare_invoice_data(
        self, 
        company_id: UUID, 
        client_id: UUID, 
        candidate_ids: List[UUID], 
        manual_totals: ManualTotals,
        invoice_number: str,
        invoice_date: date
    ) -> Dict[str, Any]:
        """
        Aggregates all necessary data for invoice generation.
        """
        # 1. Company Data
        company = self.db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("Company not found")

        # 2. Client Data
        client = self.db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise ValueError("Client not found")

        # 3. Candidates Data
        candidates = self.db.query(Candidate).filter(Candidate.id.in_(candidate_ids)).all()
        # Sort or maintain order? `in_` does not guarantee order. 
        # We might want to sort by created_at or preserve input order. 
        # For now, let's just use retrieved list.

        # 4. Column Config
        config = get_client_column_config(self.db, client_id)
        columns = config.column_definitions.get("columns", []) if config else []
        
        # If no config, default to basic columns?
        if not columns:
            columns = [
                {"field_name": "candidate_name", "display_label": "Candidate Name", "width": 2.0},
                {"field_name": "amount", "display_label": "Amount", "width": 1.0}
            ]

        # 5. Structure Line Items
        line_items = []
        for index, cand in enumerate(candidates, start=1):
            item = {"serial_no": index}
            # Flatten candidate_data for easy access
            data = cand.candidate_data
            if not data: 
                data = {}
            
            # Map columns
            # We need to map `field_name` from config to key in `candidate_data`.
            # Note: `amount` is in `candidate_data`.
            for col in columns:
                fname = col.get("field_name")
                # Special handling if needed, or just direct fetch
                # If field is not in data, empty string
                val = data.get(fname, "")
                item[fname] = val
            
            # Ensure amount is accessible if not in columns explicitly (though it should be)
            item["amount"] = data.get("amount", 0)
            line_items.append(item)

        # 6. Return Structured Dict
        return {
            "invoice_number": invoice_number,
            "invoice_date": invoice_date.strftime("%d-%b-%Y"),
            "company": {
                "name": company.name,
                "address": "Company Address Here", # TODO: Company model needs address fields? 
                # Company model has `tenant_id` etc, but looking at structure, maybe not full address fields?
                # Assuming company has some address field or we use placeholders if missing.
                # Checking `company.py` content earlier... it showed `logo_url`, `banner_url`.
                # If address missing, use placeholder.
                "gstin": "GSTIN_PLACEHOLDER", 
            },
            "client": {
                "name": client.client_name,
                "address": client.client_address,
                "gstin": client.gstin
            },
            "columns": columns,
            "line_items": line_items,
            "financials": manual_totals.model_dump()
        }

    def generate_docx(self, data: Dict[str, Any]) -> str:
        """
        Generates DOCX file and returns relative URL.
        """
        doc = Document()
        
        # --- Header / Company Info ---
        # Add Logo/Banner if available (logic skipped for brevity, generic header used)
        doc.add_heading(data["company"]["name"], 0)
        doc.add_paragraph(f"Invoice #: {data['invoice_number']}")
        doc.add_paragraph(f"Date: {data['invoice_date']}")
        
        doc.add_paragraph("BILL TO:")
        client_p = doc.add_paragraph()
        client_p.add_run(f"{data['client']['name']}\n").bold = True
        client_p.add_run(f"{data['client']['address']}\n")
        client_p.add_run(f"GSTIN: {data['client']['gstin']}")

        doc.add_paragraph() # Spacer

        # --- Line Items Table ---
        columns = data["columns"]
        # Add Serial No column implicitly?
        # Let's add Serial No + Configured Columns
        table = doc.add_table(rows=1, cols=len(columns) + 1) # +1 for S.No
        table.style = 'Table Grid'
        
        # Header Row
        hdr_cells = table.rows[0].cells
        hdr_cells[0].text = "S.No"
        for i, col in enumerate(columns):
            hdr_cells[i+1].text = col.get("display_label", col.get("field_name"))

        # Data Rows
        for item in data["line_items"]:
            row_cells = table.add_row().cells
            row_cells[0].text = str(item["serial_no"])
            for i, col in enumerate(columns):
                fname = col.get("field_name")
                val = item.get(fname, "")
                row_cells[i+1].text = str(val)

        doc.add_paragraph() # Spacer

        # --- Financial Summary (Manual Totals) ---
        # Create a smaller table aligned right? Or just logic.
        totals = data["financials"]
        
        summary_table = doc.add_table(rows=0, cols=2)
        summary_table.alignment = WD_TABLE_ALIGNMENT.RIGHT
        
        def add_summary_row(label, value, bold=False):
            r = summary_table.add_row()
            c = r.cells
            c[0].text = label
            c[1].text = f"{float(value):.2f}"
            if bold:
                c[0].paragraphs[0].runs[0].bold = True
                c[1].paragraphs[0].runs[0].bold = True

        add_summary_row("Sub Total", totals["subtotal"])
        if totals["cgst_amount"] > 0:
            add_summary_row("CGST", totals["cgst_amount"])
        if totals["sgst_amount"] > 0:
            add_summary_row("SGST", totals["sgst_amount"])
        if totals["igst_amount"] > 0:
            add_summary_row("IGST", totals["igst_amount"])
            
        add_summary_row("Grand Total", totals["grand_total"], bold=True)

        # --- Save ---
        filename = f"{data['invoice_number']}.docx"
        file_path = os.path.join(INVOICE_DIR, filename)
        doc.save(file_path)
        
        # Return URL (relative to static mount)
        return f"/static/invoices/{filename}"

def generate_invoice(
    db: Session,
    company_id: UUID, 
    client_id: UUID, 
    candidate_ids: List[UUID], 
    manual_totals: ManualTotals,
    invoice_number: str,
    invoice_date: date
) -> Invoice:
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
        candidate_ids=[str(cid) for cid in candidate_ids], # Storing as list of strings or JSONB
        subtotal=manual_totals.subtotal,
        cgst_amount=manual_totals.cgst_amount,
        sgst_amount=manual_totals.sgst_amount,
        igst_amount=manual_totals.igst_amount,
        grand_total=manual_totals.grand_total,
        file_url=file_url,
        status="GENERATED"
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    
    return db_invoice
