#!/usr/bin/env python3
"""
Startup validation script for the AI Travel Advisor backend
"""
import os
import sys
import logging
import requests
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class StartupValidator:
    """Validates all components required for the backend to start successfully"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_environment_variables(self):
        """Validate required environment variables"""
        logger.info("Validating environment variables...")
        
        required_vars = {
            "OPENAI_API_KEY": "OpenAI API key for AI functionality",
            "DATABASE_URL": "Database connection URL"
        }
        
        for var, description in required_vars.items():
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var} ({description})")
            else:
                logger.info(f"[OK] {var} is set")
        
        # Check optional variables
        optional_vars = {
            "PORT": "Server port (default: 8000)",
            "LOG_LEVEL": "Logging level (default: info)",
            "ENVIRONMENT": "Environment mode (default: development)"
        }
        
        for var, description in optional_vars.items():
            if os.getenv(var):
                logger.info(f"✓ {var} is set: {os.getenv(var)}")
            else:
                logger.info(f"[INFO] {var} not set, using default ({description})")
    
    def validate_database_connection(self):
        """Validate database connection"""
        logger.info("Validating database connection...")
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            self.errors.append("Cannot validate database connection: DATABASE_URL not set")
            return
        
        try:
            # Create engine with timeout
            engine = create_engine(
                database_url,
                pool_pre_ping=True,
                connect_args={"connect_timeout": 10}
            )
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
            
            logger.info("[OK] Database connection successful")
            
        except Exception as e:
            self.errors.append(f"Database connection failed: {e}")
    
    def validate_openai_api(self):
        """Validate OpenAI API key and connectivity"""
        logger.info("Validating OpenAI API...")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.errors.append("Cannot validate OpenAI API: OPENAI_API_KEY not set")
            return
        
        try:
            # Test OpenAI API with a simple request
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Simple test request
            test_data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 5
            }
            
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("[OK] OpenAI API connection successful")
            elif response.status_code == 401:
                self.errors.append("OpenAI API key is invalid")
            elif response.status_code == 429:
                self.warnings.append("OpenAI API rate limit reached (this is normal for testing)")
            else:
                self.errors.append(f"OpenAI API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.Timeout:
            self.warnings.append("OpenAI API timeout (network may be slow)")
        except requests.exceptions.RequestException as e:
            self.errors.append(f"OpenAI API connection failed: {e}")
    
    def validate_external_services(self):
        """Validate external service dependencies"""
        logger.info("Validating external services...")
        
        # Test weather API
        try:
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true",
                timeout=10
            )
            if response.status_code == 200:
                logger.info("[OK] Weather API accessible")
            else:
                self.warnings.append(f"Weather API returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.warnings.append(f"Weather API not accessible: {e}")
        
        # Test geocoding service
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search?q=London&format=json&limit=1",
                timeout=10
            )
            if response.status_code == 200:
                logger.info("[OK] Geocoding service accessible")
            else:
                self.warnings.append(f"Geocoding service returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            self.warnings.append(f"Geocoding service not accessible: {e}")
    
    def validate_file_permissions(self):
        """Validate file system permissions"""
        logger.info("Validating file permissions...")
        
        # Check if we can create log files
        try:
            test_log_file = "test_backend.log"
            with open(test_log_file, "w") as f:
                f.write("test")
            os.remove(test_log_file)
            logger.info("[OK] File system write permissions OK")
        except Exception as e:
            self.errors.append(f"Cannot write to file system: {e}")
    
    def run_validation(self):
        """Run all validation checks"""
        logger.info("Starting backend validation...")
        
        self.validate_environment_variables()
        self.validate_database_connection()
        self.validate_openai_api()
        self.validate_external_services()
        self.validate_file_permissions()
        
        # Report results
        logger.info("\n" + "="*50)
        logger.info("VALIDATION RESULTS")
        logger.info("="*50)
        
        if self.errors:
            logger.error(f"[ERROR] {len(self.errors)} ERRORS FOUND:")
            for error in self.errors:
                logger.error(f"  - {error}")
        
        if self.warnings:
            logger.warning(f"[WARNING] {len(self.warnings)} WARNINGS:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            logger.info("[SUCCESS] All validations passed!")
        
        if not self.errors:
            logger.info("[SUCCESS] Backend is ready to start!")
            return True
        else:
            logger.error("[ERROR] Backend cannot start due to errors")
            return False

def main():
    """Main validation function"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    validator = StartupValidator()
    success = validator.run_validation()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
