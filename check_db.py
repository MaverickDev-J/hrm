
import sys
import os
from uuid import UUID

# Add current directory to path so we can import app modules
sys.path.append(os.getcwd())

from app.database.session import SessionLocal
from app.models.company import Company

def check_company(company_id_str):
    db = SessionLocal()
    try:
        company_id = UUID(company_id_str)
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            print(f"Company {company_id} not found.")
            return

        print(f"Company: {company.name}")
        print(f"ID: {company.id}")
        print("-" * 20)
        print(f"logo_url: {company.logo_url}")
        print(f"banner_image_url: {company.banner_image_url}")
        print(f"signature_url: {company.signature_url}")
        print(f"stamp_url: {company.stamp_url}")
        print("-" * 20)
    finally:
        db.close()

if __name__ == "__main__":
    check_company("ba8445f9-fa6a-4838-922e-423defddc3d1")
