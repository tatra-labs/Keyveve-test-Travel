import os
from typing import Optional

class Config:
    """Configuration class for the frontend application"""
    
    # API Configuration
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
    
    # Streamlit Configuration
    PAGE_TITLE: str = "AI Travel Advisor"
    PAGE_ICON: str = "✈️"
    LAYOUT: str = "wide"
    
    # UI Configuration
    MAIN_HEADER_COLOR: str = "#1f77b4"
    PAGE_HEADER_COLOR: str = "#2c3e50"
    ACCENT_COLOR: str = "#3498db"
    
    @classmethod
    def get_api_url(cls) -> str:
        """Get the API base URL"""
        return cls.API_BASE_URL
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        try:
            import requests
            response = requests.get(f"{cls.API_BASE_URL.replace('/api/v1', '')}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
