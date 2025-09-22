#!/usr/bin/env python3
"""
Database operations and utilities for the AI Travel Advisor backend
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .models import Destination, KnowledgeBase
from .schemas import DestinationCreate, KnowledgeBaseCreate
from .utils import DatabaseUtils, ValidationUtils

logger = logging.getLogger(__name__)

class DestinationOperations:
    """Operations related to destinations"""
    
    @staticmethod
    def get_all_destinations(db: Session) -> List[Destination]:
        """Get all destinations"""
        destinations = db.query(Destination).all()
        logger.info(f"Retrieved {len(destinations)} destinations")
        return destinations
    
    @staticmethod
    def create_destination(db: Session, destination_data: DestinationCreate) -> Destination:
        """Create a new destination"""
        # Validate input
        name = ValidationUtils.validate_non_empty_string(destination_data.name, "Destination name")
        
        # Check if destination already exists
        existing = db.query(Destination).filter(Destination.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Destination already exists")
        
        # Create new destination
        db_destination = Destination(name=name)
        db.add(db_destination)
        db.commit()
        db.refresh(db_destination)
        
        logger.info(f"Created destination: {db_destination.name} (ID: {db_destination.id})")
        return db_destination
    
    @staticmethod
    def delete_destination(db: Session, destination_id: int) -> Dict[str, str]:
        """Delete a destination and its associated notes"""
        # Validate destination ID
        ValidationUtils.validate_destination_id(destination_id)
        
        # Get destination and count of associated notes
        destination, note_count = DatabaseUtils.get_destination_with_notes_count(db, destination_id)
        
        # Delete destination (cascade will automatically delete associated notes)
        db.delete(destination)
        db.commit()
        
        logger.info(f"Deleted destination: {destination.name} (ID: {destination_id}) with {note_count} associated notes")
        return {"message": f"Destination deleted successfully (removed {note_count} associated notes)"}

class NotesOperations:
    """Operations related to notes/knowledge base"""
    
    @staticmethod
    def get_notes_for_destination(db: Session, destination_id: int) -> List[KnowledgeBase]:
        """Get all notes for a destination"""
        # Validate destination exists
        ValidationUtils.validate_destination_exists(db, destination_id)
        
        # Get notes
        notes = db.query(KnowledgeBase).filter(KnowledgeBase.destination_id == destination_id).all()
        logger.info(f"Retrieved {len(notes)} notes for destination {destination_id}")
        return notes
    
    @staticmethod
    def create_note(db: Session, destination_id: int, note_data: KnowledgeBaseCreate) -> KnowledgeBase:
        """Create a new note for a destination"""
        # Validate inputs
        ValidationUtils.validate_destination_id(destination_id)
        content = ValidationUtils.validate_non_empty_string(note_data.content, "Note content")
        
        # Validate destination exists
        ValidationUtils.validate_destination_exists(db, destination_id)
        
        # Create note
        db_note = KnowledgeBase(destination_id=destination_id, content=content)
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        logger.info(f"Created note for destination {destination_id} (Note ID: {db_note.id})")
        return db_note

class AIOperations:
    """Operations related to AI queries"""
    
    @staticmethod
    def process_ai_query(db: Session, destination_id: int, question: str) -> Dict[str, Any]:
        """Process an AI query for a destination"""
        from .ai_service import ai_service
        
        # Validate inputs
        ValidationUtils.validate_destination_id(destination_id)
        question = ValidationUtils.validate_non_empty_string(question, "Question")
        
        # Validate destination exists
        ValidationUtils.validate_destination_exists(db, destination_id)
        
        # Process the query using AI service
        try:
            result = ai_service.process_query(db, destination_id, question)
            logger.info(f"AI query processed for destination {destination_id}")
            return result
        except Exception as ai_error:
            logger.error(f"AI service error: {ai_error}")
            # Return a fallback response instead of failing completely
            return {
                "answer": "I apologize, but I'm experiencing technical difficulties. Please try again later or contact support if the issue persists.",
                "weather_info": None
            }

# Import HTTPException here to avoid circular imports
from fastapi import HTTPException
