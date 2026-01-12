from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.client import Client
from app.models.client_column_config import ClientColumnConfig
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate
from app.schemas.client_column_config import ClientColumnConfigCreate, ClientColumnConfigUpdate


class ClientServiceError(Exception):
    """Base exception for client service errors."""
    pass


class ClientNotFoundError(ClientServiceError):
    """Raised when a client is not found."""
    def __init__(self, message: str = "Client not found"):
        self.message = message
        super().__init__(self.message)


def get_client(db: Session, client_id: UUID) -> Optional[Client]:
    """Get a single client by ID."""
    return db.query(Client).filter(Client.id == client_id).first()


def get_clients(
    db: Session, 
    company_id: Optional[UUID] = None,
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    is_active: Optional[bool] = None
) -> dict:
    """
    Get list of clients with filtering.
    """
    query = db.query(Client)
    
    if company_id:
        query = query.filter(Client.company_id == company_id)
        
    if is_active is not None:
        query = query.filter(Client.is_active == is_active)
        
    if search:
        search_filter = Client.client_name.ilike(f"%{search}%")
        query = query.filter(search_filter)
        
    total = query.count()
    clients = query.offset(skip).limit(limit).all()
    
    return {
        "clients": clients,
        "total": total,
        "page": (skip // limit) + 1,
        "limit": limit
    }


def create_client(db: Session, client_in: ClientCreate, company_id: UUID) -> Client:
    """
    Create a new client for a company.
    """
    db_client = Client(
        **client_in.model_dump(),
        company_id=company_id
    )
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def update_client(
    db: Session, 
    db_client: Client, 
    client_in: ClientUpdate
) -> Client:
    """
    Update a client.
    """
    update_data = client_in.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_client, field, value)

    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def soft_delete_client(db: Session, db_client: Client) -> Client:
    """
    Soft delete a client (set is_active=False).
    """
    db_client.is_active = False
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client


def get_client_column_config(db: Session, client_id: UUID) -> Optional[ClientColumnConfig]:
    """
    Get column configuration for a specific client.
    """
    return db.query(ClientColumnConfig).filter(ClientColumnConfig.client_id == client_id).first()


def upsert_client_column_config(
    db: Session, 
    client_id: UUID, 
    config_in: ClientColumnConfigCreate
) -> ClientColumnConfig:
    """
    Create or update column configuration for a client.
    """
    db_config = get_client_column_config(db, client_id)
    
    if db_config:
        # Update existing
        db_config.column_definitions = config_in.model_dump(mode='json')
    else:
        # Create new
        db_config = ClientColumnConfig(
            client_id=client_id,
            column_definitions=config_in.model_dump(mode='json')
        )
        db.add(db_config)
    
    db.commit()
    db.refresh(db_config)
    return db_config
