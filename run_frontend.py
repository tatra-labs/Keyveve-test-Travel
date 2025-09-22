#!/usr/bin/env python3
"""
Script to run the Streamlit frontend
"""
import subprocess
import sys
import os

if __name__ == "__main__":
    # Change to frontend directory
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.port", "8501",
        # "--server.address", "0.0.0.0"
    ], cwd=frontend_dir)
