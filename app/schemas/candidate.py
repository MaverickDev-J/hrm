from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

class CandidateBase(BaseModel):
    # Flexible data payload + fixed Amount
    candidate_data: Dict[str, Any] = Field(..., description="Dynamic candidate fields. MUST contain 'amount'.")
    is_active: bool = True

    @field_validator('candidate_data')
    def validate_amount_presence(cls, v):
        if not v:
            raise ValueError("candidate_data cannot be empty")
        # Check case-insensitive 'amount' or just match strictly 'amount' as per key decision
        # The prompt says 'amount' (lowercase) is the required field.
        if 'amount' not in v:
            raise ValueError("candidate_data must contain required field 'amount' (numeric)")
        
        # Verify it is numeric 
        try:
            float(v['amount'])
        except (ValueError, TypeError):
             raise ValueError("'amount' field must be a valid number")
        
        return v

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    candidate_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @field_validator('candidate_data')
    def validate_amount_if_present(cls, v):
        if v and 'amount' in v:
            try:
                float(v['amount'])
            except (ValueError, TypeError):
                 raise ValueError("'amount' field must be a valid number")
        return v

class CandidateResponse(CandidateBase):
    id: uuid.UUID
    client_id: uuid.UUID
    company_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CandidateListResponse(BaseModel):
    candidates: list[CandidateResponse]
    total: int
    page: int
    limit: int
