import sys
import os
from sqlalchemy.orm import Session

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.session import SessionLocal
from app.services.auth_service import create_user, get_user_by_email
from app.core.config import settings

def create_superadmin() -> None:
    """
    Create a superuser if one does not exist.
    """
    db: Session = SessionLocal()
    try:
        email = "admin@example.com"
        password = "StrongPassword123"
        
        user = get_user_by_email(db, email=email)
        if user:
            print(f"Superuser {email} already exists.")
            return

        print(f"Creating superuser {email}...")
        create_user(
            db=db,
            email=email,
            password=password,
            full_name="System Administrator",
            is_superuser=True
        )
        print("Superuser created successfully!")
        
    except Exception as e:
        print(f"Error creating superuser: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Running superadmin seed script...")
    create_superadmin()
