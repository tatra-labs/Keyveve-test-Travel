#!/usr/bin/env python3
"""
Script to run the FastAPI backend server with robust configuration
"""
import uvicorn
import os
import sys
import logging
from pathlib import Path

# Add backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

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

def main():
    """Main function to run the backend server"""
    try:
        logger.info("Starting AI Travel Advisor Backend Server...")
        
        # Check for required environment variables
        required_env_vars = ["OPENAI_API_KEY", "DATABASE_URL"]
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
            logger.warning("Please check your .env file or environment configuration")
        
        # Server configuration
        config = {
            "app": "backend.main:app",
            "host": "0.0.0.0",
            "port": int(os.getenv("PORT", 8000)),
            "reload": os.getenv("RELOAD", "true").lower() == "true",
            "reload_dirs": ["backend"] if os.getenv("RELOAD", "true").lower() == "true" else None,
            "log_level": os.getenv("LOG_LEVEL", "info").lower(),
            "workers": int(os.getenv("WORKERS", 1)),
            "access_log": True,
            "use_colors": True,
            "loop": "asyncio",
            "http": "httptools",
            "timeout_keep_alive": 30,
            "timeout_graceful_shutdown": 30,
            "limit_concurrency": 1000,
            "limit_max_requests": 10000,
            "backlog": 2048,
        }
        
        # Production-specific settings
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            config.update({
                "reload": False,
                "reload_dirs": None,  # Remove reload_dirs in production
                "workers": int(os.getenv("WORKERS", 4)),
                "log_level": "warning",
                "access_log": False,
            })
            logger.info("Running in production mode")
        else:
            logger.info("Running in development mode")
        
        logger.info(f"Server configuration: {config}")
        
        # Start the server
        uvicorn.run(**config)
        
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
