import os
import shutil
from typing import Optional
from uuid import UUID

from fastapi import UploadFile, HTTPException, status

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB


def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file type and size.
    Note: Size check here is approximate based on content-length header if available,
    or we rely on reading chunks. For simplicity, we check extension here.
    """
    filename = file.filename or ""
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )


async def save_upload_file(
    file: UploadFile, 
    company_id: UUID, 
    file_type: str
) -> str:
    """
    Save uploaded file to disk and return the relative URL.
    Path: static/uploads/companies/{company_id}/{file_type}.{ext}
    """
    validate_image_file(file)
    
    company_dir = os.path.join(UPLOAD_DIR, "companies", str(company_id))
    os.makedirs(company_dir, exist_ok=True)
    
    filename = file.filename or ""
    extension = filename.split(".")[-1].lower()
    
    # Save as {file_type}.{ext} (e.g., logo.png)
    # We might want to remove old files of same type but different ext? 
    # For now, just overwrite same name.
    
    # Clean up existing files of this type (e.g. if we have logo.jpg and uploading logo.png)
    for ext in ALLOWED_EXTENSIONS:
        existing_path = os.path.join(company_dir, f"{file_type}.{ext}")
        if os.path.exists(existing_path):
            os.remove(existing_path)
            
    final_filename = f"{file_type}.{extension}"
    file_path = os.path.join(company_dir, final_filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not save file: {str(e)}"
        )
        
    # Return URL path
    return f"/static/uploads/companies/{str(company_id)}/{final_filename}"
