import logging
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .database import get_db, get_connection_pool_status
from .models import Destination, KnowledgeBase
from .schemas import DestinationCreate, Destination as DestinationSchema, KnowledgeBaseCreate, KnowledgeBase as KnowledgeBaseSchema, AIQuery, AIResponse
from .db_operations import DestinationOperations, NotesOperations, AIOperations
from .utils import destination_endpoint, ai_endpoint, notes_endpoint, RateLimiter

logger = logging.getLogger(__name__)
router = APIRouter()

# Destination endpoints
@router.get("/destinations", response_model=List[DestinationSchema])
@destination_endpoint
def get_destinations(request: Request, db: Session = Depends(get_db)):
    """Get all destinations"""
    return DestinationOperations.get_all_destinations(db)

@router.post("/destinations", response_model=DestinationSchema)
@destination_endpoint
def create_destination(
    destination: DestinationCreate, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Create a new destination"""
    return DestinationOperations.create_destination(db, destination)

@router.delete("/destinations/{destination_id}")
@destination_endpoint
def delete_destination(
    destination_id: int, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Delete a destination"""
    return DestinationOperations.delete_destination(db, destination_id)

# Knowledge Base endpoints
@router.get("/destinations/{destination_id}/notes", response_model=List[KnowledgeBaseSchema])
@notes_endpoint
def get_notes(destination_id: int, request: Request, db: Session = Depends(get_db)):
    """Get all notes for a destination"""
    return NotesOperations.get_notes_for_destination(db, destination_id)

@router.post("/destinations/{destination_id}/notes", response_model=KnowledgeBaseSchema)
@notes_endpoint
def create_note(
    destination_id: int, 
    note: KnowledgeBaseCreate, 
    request: Request, 
    db: Session = Depends(get_db)
):
    """Create a new note for a destination"""
    return NotesOperations.create_note(db, destination_id, note)

# AI endpoint
@router.post("/ask", response_model=AIResponse)
@ai_endpoint
def ask_ai(query: AIQuery, request: Request, db: Session = Depends(get_db)):
    """Ask AI a question about a destination"""
    result = AIOperations.process_ai_query(db, query.destination_id, query.question)
    return AIResponse(
        answer=result["answer"],
        weather_info=result["weather_info"]
    )

# Additional monitoring endpoints
@router.get("/status")
def get_status():
    """Get system status and connection pool information"""
    try:
        pool_status = get_connection_pool_status()
        rate_limit_stats = RateLimiter.get_rate_limit_stats()
        
        return {
            "status": "healthy",
            "database_pool": pool_status,
            "rate_limits": rate_limit_stats
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get status")
