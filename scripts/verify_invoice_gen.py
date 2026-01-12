import sys
import os
# Add root to sys.path
sys.path.append(os.getcwd())

from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.utils.security import create_access_token
from app.database.session import SessionLocal
from app.models.user import User
from app.models.company import Company

client = TestClient(app)

def verify_invoice_flow():
    print("🚀 Starting Invoice Generation Verification...")
    
    db = SessionLocal()
    
    try:
        # 1. Setup Data - Ensure we have a company and admin
        # Using a fixed email for test
        email = "invoice_admin@test.com"
        password = "password123"
        
        # Ensure Company
        company = db.query(Company).filter(Company.name == "Test Company Inc").first()
        if not company:
            company = Company(name="Test Company Inc", tenant_id="test-co", subdomain="testco")
            db.add(company)
            db.commit()
            print("✅ Created Test Company")
        
        # Ensure User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            from app.core.security import get_password_hash
            user = User(
                email=email,
                hashed_password=get_password_hash(password),
                full_name="Invoice Admin",
                role_id=1, # Assuming 1 is Admin/Owner or valid role
                company_id=company.id,
                is_active=True
            )
            db.add(user)
            db.commit()
            print("✅ Created Test Admin")
        else:
            print("ℹ️ Test Admin exists")

        # Login
        token = create_access_token(user.id)
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Create Client
        client_data = {
            "client_name": "Athena BPO Test",
            "client_address": "Cyber City, Gurgaon",
            "city": "Gurgaon",
            "state": "Haryana",
            "pincode": "122002",
            "gstin": "06AAAAA0000A1Z5",
            "pan_number": "AAAAA0000A"
        }
        resp = client.post("/api/v1/clients/", json=client_data, headers=headers)
        if resp.status_code not in [200, 201]:
             print(f"❌ Failed to create client: {resp.text}")
             return
        
        client_id = resp.json()["id"]
        print(f"✅ Created Client: {client_id}")

        # 3. Configure Columns
        config_data = {
            "columns": [
                {"field_name": "candidate_name", "display_label": "Name", "width": "2.0", "order": 1},
                {"field_name": "process", "display_label": "Process", "width": "1.5", "order": 2},
                {"field_name": "amount", "display_label": "Amount (INR)", "width": "1.0", "order": 3}
            ]
        }
        resp = client.put(f"/api/v1/clients/{client_id}/config", json=config_data, headers=headers)
        if resp.status_code != 200:
             print(f"❌ Failed to configure columns: {resp.text}")
             return
        print("✅ Configured Invoice Columns")

        # 4. Add Candidate
        candidate_data = {
            "candidate_data": {
                "candidate_name": "Siddhant Test",
                "process": "Voice Support",
                "amount": 154500.00
            },
            "is_active": True
        }
        resp = client.post(f"/api/v1/clients/{client_id}/candidates", json=candidate_data, headers=headers)
        if resp.status_code != 201:
             print(f"❌ Failed to create candidate: {resp.text}")
             return
        
        cand_id = resp.json()["id"]
        print(f"✅ Added Candidate: {cand_id}")

        # 5. Generate Invoice (Manual Totals)
        invoice_req = {
            "client_id": client_id,
            "candidate_ids": [cand_id],
            "invoice_number": f"INV-TEST-{os.urandom(2).hex()}",
            "invoice_date": "2024-01-27",
            "manual_totals": {
                "subtotal": 9000.00,
                "cgst_amount": 0.00,
                "sgst_amount": 0.00,
                "igst_amount": 0.00,
                "grand_total": 9000.00
            }
        }
        
        resp = client.post("/api/v1/invoices/generate", json=invoice_req, headers=headers)
        if resp.status_code != 201:
             print(f"❌ Invoice Generation Failed: {resp.text}")
             return
        
        data = resp.json()
        print(f"✅ Generated Invoice: {data['invoice_number']}")
        print(f"📄 File URL: {data['file_url']}")
        print(f"💰 Grand Total: {data['grand_total']} (Should be 9000.0, matching manual input)")

        # Verify File Exists
        # The URL is relative /static/invoices/...
        # We check file system
        file_path = f".{data['file_url']}" # ./static/...
        if os.path.exists(file_path):
             print("✅ DOCX File verified on disk")
        else:
             print(f"❌ File missing at {file_path}")

    except Exception as e:
        print(f"❌ Exception: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_invoice_flow()
