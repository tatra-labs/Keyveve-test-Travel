import logging
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from .routes import router
from .database import engine, get_db
from .models import Base

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("backend.log")
    ]
)
logger = logging.getLogger(__name__)

# Global variable to track shutdown state
shutdown_event = asyncio.Event()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting AI Travel Advisor API...")
    
    try:
        # Run startup validation
        from .startup_validator import StartupValidator
        validator = StartupValidator()
        
        logger.info("Running startup validation...")
        if not validator.run_validation():
            logger.error("Startup validation failed")
            raise RuntimeError("Startup validation failed")
        
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Test database connection
        db = next(get_db())
        db.close()
        logger.info("Database connection verified")
        
        # Initialize AI service
        try:
            from .ai_service import ai_service
            logger.info("AI service initialized successfully")
        except Exception as e:
            logger.warning(f"AI service initialization warning: {e}")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Travel Advisor API...")
    shutdown_event.set()
    logger.info("Application shutdown complete")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="AI Travel Advisor API",
    description="Backend API for AI Travel Advisor application",
    version="1.0.0",
    lifespan=lifespan
)

# Add security middleware
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["*"]  # In production, specify actual hosts
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )

# Database exception handler
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(request, exc):
    logger.error(f"Database error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Database error occurred"}
    )

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "AI Travel Advisor API is running!", "status": "healthy"}

@app.get("/health")
def health_check():
    """Enhanced health check endpoint"""
    try:
        # Test database connection
        db = next(get_db())
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "shutdown_requested": shutdown_event.is_set()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/ready")
def readiness_check():
    """Readiness check for Kubernetes/Docker"""
    try:
        # Test database connection
        db = next(get_db())
        db.close()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(status_code=503, detail="Service not ready")

@app.get("/metrics")
def get_metrics():
    """Get application metrics for monitoring"""
    try:
        from .database import get_connection_pool_status
        
        pool_status = get_connection_pool_status()
        
        # Calculate request metrics using the centralized rate limiter
        from .utils import RateLimiter
        rate_limit_stats = RateLimiter.get_rate_limit_stats()
        
        # Get memory usage (basic)
        import psutil
        memory_info = psutil.virtual_memory()
        
        return {
            "database_pool": pool_status,
            "requests": rate_limit_stats,
            "system": {
                "memory_usage_percent": memory_info.percent,
                "memory_available_gb": round(memory_info.available / (1024**3), 2),
                "cpu_count": psutil.cpu_count()
            },
            "application": {
                "uptime_seconds": time.time() - getattr(get_metrics, 'start_time', time.time()),
                "shutdown_requested": shutdown_event.is_set()
            }
        }
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics")

# Initialize start time for uptime calculation
import time
get_metrics.start_time = time.time()

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_event.set()

# Register signal handlers
if hasattr(signal, 'SIGINT'):
    signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

# Request logging middleware
@app.middleware("http")
async def request_logging_middleware(request, call_next):
    """Middleware to log requests and handle graceful shutdown"""
    start_time = time.time()
    
    # Check for graceful shutdown
    if shutdown_event.is_set():
        return JSONResponse(
            status_code=503,
            content={"detail": "Service is shutting down"}
        )
    
    # Log request
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} in {process_time:.3f}s")
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request error: {e} in {process_time:.3f}s")
        raise
