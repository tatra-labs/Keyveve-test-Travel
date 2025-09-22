#!/usr/bin/env python3
"""
Common utilities and shared functionality for the AI Travel Advisor backend
"""
import logging
import time
import functools
from typing import Callable, Any, Dict, Optional
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis or similar)
request_counts: Dict[str, list] = {}

class RateLimiter:
    """Rate limiting utility class"""
    
    @staticmethod
    def check_rate_limit(client_ip: str, limit: int = 100, window: int = 3600) -> bool:
        """Simple rate limiting check"""
        current_time = time.time()
        if client_ip not in request_counts:
            request_counts[client_ip] = []
        
        # Remove old requests outside the window
        request_counts[client_ip] = [
            req_time for req_time in request_counts[client_ip] 
            if current_time - req_time < window
        ]
        
        # Check if limit exceeded
        if len(request_counts[client_ip]) >= limit:
            return False
        
        # Add current request
        request_counts[client_ip].append(current_time)
        return True
    
    @staticmethod
    def get_client_ip(request: Request) -> str:
        """Extract client IP from request"""
        return request.client.host if request.client else "unknown"
    
    @staticmethod
    def get_rate_limit_stats() -> Dict[str, Any]:
        """Get rate limiting statistics"""
        total_requests = sum(len(requests) for requests in request_counts.values())
        active_clients = len(request_counts)
        rate_limited_clients = len([
            client for client, requests in request_counts.items() 
            if len(requests) >= 100
        ])
        
        return {
            "total_requests": total_requests,
            "active_clients": active_clients,
            "rate_limited_clients": rate_limited_clients
        }

class ErrorHandler:
    """Centralized error handling utilities"""
    
    @staticmethod
    def handle_database_errors(func: Callable) -> Callable:
        """Decorator to handle database-related errors consistently"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except IntegrityError as e:
                logger.error(f"Integrity error in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail="Data integrity error occurred")
            except SQLAlchemyError as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail="Database error occurred")
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
        return wrapper
    
    @staticmethod
    def handle_database_rollback(db: Session, func: Callable) -> Callable:
        """Decorator to handle database rollback on errors"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                db.rollback()
                raise
            except Exception as e:
                db.rollback()
                raise
        return wrapper

class TimingLogger:
    """Timing and logging utilities"""
    
    @staticmethod
    def log_execution_time(func: Callable) -> Callable:
        """Decorator to log function execution time"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                response_time = time.time() - start_time
                logger.info(f"{func.__name__} completed in {response_time:.3f}s")
        return wrapper
    
    @staticmethod
    def log_request_info(request: Request, response_time: float):
        """Log request information for monitoring"""
        client_ip = RateLimiter.get_client_ip(request)
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Status: {getattr(request, 'status_code', 'N/A')} - "
            f"Response time: {response_time:.3f}s - "
            f"Client: {client_ip}"
        )

class ValidationUtils:
    """Input validation utilities"""
    
    @staticmethod
    def validate_destination_id(destination_id: int) -> None:
        """Validate destination ID"""
        if destination_id <= 0:
            raise HTTPException(status_code=400, detail="Invalid destination ID")
    
    @staticmethod
    def validate_non_empty_string(value: str, field_name: str) -> str:
        """Validate that a string is not empty"""
        if not value or not value.strip():
            raise HTTPException(status_code=400, detail=f"{field_name} cannot be empty")
        return value.strip()
    
    @staticmethod
    def validate_destination_exists(db: Session, destination_id: int):
        """Validate that destination exists and return it"""
        from .models import Destination
        destination = db.query(Destination).filter(Destination.id == destination_id).first()
        if not destination:
            raise HTTPException(status_code=404, detail="Destination not found")
        return destination

class DatabaseUtils:
    """Database operation utilities"""
    
    @staticmethod
    def safe_db_operation(db: Session, operation: Callable, *args, **kwargs):
        """Safely execute database operations with rollback on error"""
        try:
            return operation(db, *args, **kwargs)
        except Exception as e:
            db.rollback()
            raise e
    
    @staticmethod
    def get_destination_with_notes_count(db: Session, destination_id: int):
        """Get destination and count of associated notes"""
        from .models import Destination, KnowledgeBase
        
        destination = ValidationUtils.validate_destination_exists(db, destination_id)
        note_count = db.query(KnowledgeBase).filter(
            KnowledgeBase.destination_id == destination_id
        ).count()
        
        return destination, note_count

# Combined decorators for common patterns
def endpoint_handler(
    rate_limit: int = 100,
    rate_window: int = 3600,
    log_timing: bool = True,
    handle_db_errors: bool = True
):
    """Combined decorator for common endpoint patterns"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract request from args (assuming it's the first parameter after self)
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if request:
                # Rate limiting
                client_ip = RateLimiter.get_client_ip(request)
                if not RateLimiter.check_rate_limit(client_ip, rate_limit, rate_window):
                    raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
            # Timing
            if log_timing:
                start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                return result
            except HTTPException:
                raise
            except IntegrityError as e:
                logger.error(f"Integrity error in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail="Data integrity error occurred")
            except SQLAlchemyError as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail="Database error occurred")
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")
            finally:
                if log_timing and request:
                    response_time = time.time() - start_time
                    logger.info(f"{func.__name__} completed in {response_time:.3f}s")
        
        return wrapper
    return decorator

# Specific decorators for different endpoint types
def destination_endpoint(func: Callable) -> Callable:
    """Decorator for destination-related endpoints"""
    return endpoint_handler(rate_limit=100, rate_window=3600)(func)

def ai_endpoint(func: Callable) -> Callable:
    """Decorator for AI-related endpoints (more restrictive rate limiting)"""
    return endpoint_handler(rate_limit=50, rate_window=3600)(func)

def notes_endpoint(func: Callable) -> Callable:
    """Decorator for notes-related endpoints"""
    return endpoint_handler(rate_limit=100, rate_window=3600)(func)
