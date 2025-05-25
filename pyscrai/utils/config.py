# PyScrAI/pyscrai/utils/config.py
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field
# import dotenv

# # Load environment variables from a .env file if it exists
# dotenv.load_dotenv

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
    OPENROUTER_DEFAULT_MODEL_ID: str = Field(default="meta-llama/llama-4-maverick:free", env="OPENROUTER_DEFAULT_MODEL_ID")
    # Optional: For OpenRouter leaderboard tracking
    OPENROUTER_SITE_URL: Optional[str] = Field(default=None, env="OPENROUTER_SITE_URL")
    OPENROUTER_X_TITLE: Optional[str] = Field(default=None, env="OPENROUTER_X_TITLE")

    # LMStudio specific settings
    LMSTUDIO_BASE_URL: str = Field(default="http://localhost:1234/v1", env="LMSTUDIO_BASE_URL")
    LMSTUDIO_API_KEY: Optional[str] = Field(default=None, env="LMSTUDIO_API_KEY") # Typically not required for local LMStudio
    LMSTUDIO_DEFAULT_MODEL_ID: str = Field(default="local-model", env="LMSTUDIO_DEFAULT_MODEL_ID") # Or the specific model name served

    # Add other global settings for PyScrAI here if needed

    class Config:
        # Pydantic settings configuration
        env_file = ".env"  # Load from .env file if present
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields not defined in the model

# Instantiate settings
# This instance will be imported and used across the application
settings = Settings()

# Example of how to access a setting:
# from pyscrai.utils.config import settings
# print(settings.OPENROUTER_API_KEY)

# Additional configuration class for project paths and setup
from pathlib import Path
import os


class Config:
    """Configuration management for PyScrAI"""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    TEMPLATES_DIR = PROJECT_ROOT / "pyscrai" / "templates"
    
    # Database
    DATABASE_URL = f"sqlite:///{DATA_DIR / 'pyscrai.db'}"
    
    # Default model configurations
    DEFAULT_OPENROUTER_MODEL = "meta-llama/llama-3.1-8b-instruct:free"
    DEFAULT_LMSTUDIO_MODEL = "llama-3.1-8b-instruct"
    
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
                "id": cls.DEFAULT_OPENROUTER_MODEL,
                "temperature": 0.7,
                "api_key": os.environ.get("OPENROUTER_API_KEY")
            }
        elif provider == "lmstudio":
            return {
                "id": cls.DEFAULT_LMSTUDIO_MODEL,
                "temperature": 0.7
            }
        else:
            raise ValueError(f"Unsupported provider: {provider}")


# Initialize project directories on import
Config.ensure_directories()
