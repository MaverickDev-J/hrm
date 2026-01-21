"""
File system operations and path handling for invoice generation.

This module centralizes all file-related logic including:
- Directory management
- Path normalization (handling /static/... URLs)
- File cleanup operations
- Filename generation
"""

import os
from typing import Optional, Tuple

# ========================================
# CONSTANTS & INITIALIZATION
# ========================================

STATIC_DIR = "static"
INVOICE_DIR = os.path.join(STATIC_DIR, "invoices")

# Ensure invoice directory exists on module import
os.makedirs(INVOICE_DIR, exist_ok=True)

# ========================================
# PATH NORMALIZATION
# ========================================

def normalize_file_path(url: Optional[str]) -> Optional[str]:
    """
    Convert URL-style paths to filesystem paths.

    Handles paths that start with "/" (like /static/uploads/...)
    and converts them to relative paths usable by os.path.exists().

    Args:
        url: Path that might start with "/" (e.g., "/static/uploads/banner.png")

    Returns:
        Normalized relative path, or None if input is None/empty
    """
    if not url:
        return None

    # Convert "/static/..." -> "static/..."
    normalized = url.lstrip("/")

    if os.path.exists(normalized):
        return normalized

    # Fallback: try relative path from CWD
    with_dot = os.path.join(".", normalized)
    if os.path.exists(with_dot):
        return with_dot

    return normalized

# ========================================
# FILE CLEANUP
# ========================================

def cleanup_invoice_file(file_url: Optional[str]) -> None:
    """
    Safely delete an invoice file given its URL or relative path.

    Suppresses errors gracefully (logs warning instead of raising).

    Args:
        file_url: File URL/path (e.g., "/static/invoices/INV-001.docx")
    """
    if not file_url:
        return

    try:
        rel_path = file_url.lstrip("/")

        if os.path.exists(rel_path):
            os.remove(rel_path)
            return

        full_path = os.path.join(os.getcwd(), rel_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            return

    except Exception as e:
        print(f"Warning: Could not delete invoice file: {e}")

# ========================================
# PATH GENERATION
# ========================================

def get_invoice_file_path(invoice_number: str) -> Tuple[str, str, str]:
    """
    Generate standardized filename, filesystem path, and URL for an invoice.

    Returns:
        (filename, file_path, url)
    """
    filename = f"{invoice_number}.docx"
    file_path = os.path.join(INVOICE_DIR, filename)
    url = f"/static/invoices/{filename}"

    return filename, file_path, url

# ========================================
# TEMP FILE HANDLING
# ========================================

def get_temp_invoice_path(invoice_number: str) -> Tuple[str, str, str]:
    """
    Generate filename, path, and URL for a temporary (preview) invoice.

    Returns:
        (filename, file_path, url)
    """
    filename = f"{invoice_number}_preview.docx"
    file_path = os.path.join(INVOICE_DIR, filename)
    url = f"/static/invoices/{filename}"

    return filename, file_path, url
