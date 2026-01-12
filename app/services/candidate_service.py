from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.candidate import Candidate
from app.schemas.candidate import CandidateCreate, CandidateUpdate

def get_candidates(
    db: Session, 
    company_id: UUID,
    client_id: Optional[UUID] = None,
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None
) -> dict:
    """
    Get candidates with strict tenant isolation.
    """
    query = db.query(Candidate).filter(Candidate.company_id == company_id)
    
    if client_id:
        query = query.filter(Candidate.client_id == client_id)
        
    if search:
        # Search inside JSONB is tricky depending on DB support, 
        # but here we'll assume we search specific known fields if requested, or just simple filter.
        # For now, let's skip complex JSONB search or implement simple extraction if needed.
        # Example: Search by candidate name inside the JSON
        # Postgres JSONB search: Candidate.candidate_data['candidate_name'].astext.ilike(f"%{search}%")
        # We will need the right casting for this.
        # Let's try flexible search on the candidate_name key if it exists
        query = query.filter(Candidate.candidate_data['candidate_name'].astext.ilike(f"%{search}%"))

    total = query.count()
    candidates = query.order_by(desc(Candidate.created_at)).offset(skip).limit(limit).all()
    
    return {
        "candidates": candidates,
        "total": total,
        "page": (skip // limit) + 1,
        "limit": limit
    }

def create_candidate(
    db: Session, 
    candidate_in: CandidateCreate, 
    client_id: UUID, 
    company_id: UUID
) -> Candidate:
    """
    Create a new candidate.
    """
    db_candidate = Candidate(
        client_id=client_id,
        company_id=company_id,
        candidate_data=candidate_in.candidate_data,
        is_active=candidate_in.is_active
    )
    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def update_candidate(
    db: Session,
    candidate_id: UUID,
    candidate_in: CandidateUpdate,
    company_id: UUID
) -> Optional[Candidate]:
    """
    Update a candidate. verify ownership.
    """
    db_candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.company_id == company_id
    ).first()

    if not db_candidate:
        return None

    if candidate_in.is_active is not None:
        db_candidate.is_active = candidate_in.is_active
        
    if candidate_in.candidate_data:
        # We might want to merge or replace. 
        # Usually replace is safer for strict configs, or merge for partial updates.
        # Given the schema, let's do a shallow merge or full replace.
        # Let's do a merge of keys
        current_data = dict(db_candidate.candidate_data)
        current_data.update(candidate_in.candidate_data)
        db_candidate.candidate_data = current_data
        
        # Ensure 'amount' is still there? 
        # The schema validator on CandidateCreate checks it, but for Update it's loose.
        # However, the DB model validation doesn't enforce it unless we add a check here.
        # We trust the Pydantic schema validator used at API layer.

    db.add(db_candidate)
    db.commit()
    db.refresh(db_candidate)
    return db_candidate

def delete_candidate(db: Session, candidate_id: UUID, company_id: UUID) -> bool:
    """
    Hard delete or soft delete. Let's do soft delete if we want history, but Invoice logic might need them.
    Let's stick to soft delete via is_active usually, but here we'll just delete for simplicity 
    unless requirements say otherwise. Re-reading plan: 'Candidate Management API'.
    The model has is_active. Let's use soft delete logic if requested, or just hard delete.
    Let's do hard delete for now to keep it simple, or soft if is_active is toggled.
    """
    db_candidate = db.query(Candidate).filter(
        Candidate.id == candidate_id,
        Candidate.company_id == company_id
    ).first()
    
    if not db_candidate:
        return False
        
    db.delete(db_candidate)
    db.commit()
    return True
