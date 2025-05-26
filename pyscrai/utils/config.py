"""
Configuration management for PyScrAI
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Centralized configuration for PyScrAI application.
    Loads settings from environment variables or a .env file.
    """
    # Default LLM provider to use (e.g., "openrouter" or "lmstudio")
    PYSCRAI_DEFAULT_PROVIDER: str = Field(default="openrouter", env="PYSCRAI_DEFAULT_PROVIDER")

    # OpenRouter specific settings
    OPENROUTER_API_KEY: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    PYSCRAI_OPENROUTER_MODEL_ID: str = Field(default="meta-llama/llama-3.1-8b-instruct:free", env="PYSCRAI_OPENROUTER_MODEL_ID")
    OPENROUTER_SITE_URL: Optional[str] = Field(default=None, env="OPENROUTER_SITE_URL")
    OPENROUTER_X_TITLE: Optional[str] = Field(default=None, env="OPENROUTER_X_TITLE")

    # LMStudio specific settings
    PYSCRAI_LMSTUDIO_API_BASE: str = Field(default="http://localhost:1234/v1", env="PYSCRAI_LMSTUDIO_API_BASE")
    LMSTUDIO_API_KEY: Optional[str] = Field(default=None, env="LMSTUDIO_API_KEY")
    PYSCRAI_LMSTUDIO_MODEL_ID: str = Field(default="llama-3.1-8b-instruct", env="PYSCRAI_LMSTUDIO_MODEL_ID")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


class Config:
    """Configuration management for PyScrAI paths and defaults"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    TEMPLATES_DIR = PROJECT_ROOT / "pyscrai" / "templates"
    
    # Database
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'pyscrai.db'}"
    
    # API settings
    API_HOST = "localhost"
    API_PORT = 8000
    
    @classmethod
    def ensure_directories(cls):
        """Ensure all required directories exist"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.TEMPLATES_DIR.mkdir(exist_ok=True)
        (cls.TEMPLATES_DIR / "agents").mkdir(exist_ok=True)
        (cls.TEMPLATES_DIR / "scenarios").mkdir(exist_ok=True)
        (cls.TEMPLATES_DIR / "events").mkdir(exist_ok=True)
    
    @classmethod
    def get_model_config(cls, provider: str = "openrouter") -> Dict[str, Any]:
        """Get default model configuration"""
        if provider == "openrouter":
            return {
                "id": settings.PYSCRAI_OPENROUTER_MODEL_ID,
                "temperature": 0.7,
                "api_key": settings.OPENROUTER_API_KEY
            }
        elif provider == "lmstudio":
            return {
                "id": settings.PYSCRAI_LMSTUDIO_MODEL_ID,
                "temperature": 0.7
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Instantiate settings
settings = Settings()

# Initialize project directories on import
Config.ensure_directories()
