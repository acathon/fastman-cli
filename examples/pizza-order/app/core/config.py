"""Application configuration"""
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """Application settings"""

    # Project
    PROJECT_NAME: str = "pizza-order"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "rGiDGpcJsGaCypQsGb1Yph4Vo_6ehlBsdwY7-5B5wUo"
    ALLOWED_HOSTS: List[str] = ["*"]

    # Database (SQL)
    DATABASE_URL: Optional[str] = "sqlite:///./app.db"

    # Firebase (NoSQL)
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None

    # API
    API_V1_PREFIX: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
