#!/usr/bin/env python3
"""
Script to set up the database and run migrations
"""
import os
import sys
import subprocess
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def setup_database():
    """Set up the database"""
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/travel_advisor")
    
    print("Setting up database...")
    print(f"Database URL: {database_url}")
    
    try:
        # Test database connection
        engine = create_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Run migrations
        print("Running database migrations...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], cwd="db", capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migrations completed successfully")
        else:
            print("❌ Database migrations failed:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if setup_database():
        print("\n🎉 Database setup completed!")
        print("You can now run the backend and frontend servers.")
    else:
        print("\n💥 Database setup failed!")
        print("Please check your database configuration and try again.")
        sys.exit(1)
