"""
Application configuration management.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    """Application settings"""
    
    # Directories
    UPLOAD_DIR = Path("uploads")
    OUTPUT_DIR = Path("outputs")
    PROMPTS_DIR = Path("prompts")
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # CORS
    CORS_ORIGINS = ["*"]
    CORS_CREDENTIALS = False
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]
    
    def __init__(self):
        """Ensure directories exist"""
        self.UPLOAD_DIR.mkdir(exist_ok=True)
        self.OUTPUT_DIR.mkdir(exist_ok=True)
        self.PROMPTS_DIR.mkdir(exist_ok=True, parents=True)

# Global settings instance
settings = Settings()
