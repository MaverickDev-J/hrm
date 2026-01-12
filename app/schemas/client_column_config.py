from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime
from pydantic import BaseModel, Field

class ColumnDefinition(BaseModel):
    field_name: str
    display_label: str
    column_width: str = "1.0" # inches, string
    is_required: bool = False
    order: int = 0

class ClientColumnConfigBase(BaseModel):
    # Wrapper for the JSONB column_definitions
    # Expected structure: {"columns": [ ... ]}
    columns: List[ColumnDefinition]

class ClientColumnConfigCreate(ClientColumnConfigBase):
    pass

class ClientColumnConfigUpdate(ClientColumnConfigBase):
    pass

class ClientColumnConfigResponse(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    column_definitions: Dict[str, Any] # Returns the full JSON object
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
