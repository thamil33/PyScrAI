"""
Configuration management for the LangGraph Multi-Agent Simulation Framework.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from dotenv import load_dotenv


class LLMProviderConfig(BaseModel):
    """Configuration for LLM providers."""
    api_key: str
    base_url: str
    default_model: str
    fallback_models: List[str] = Field(default_factory=list)
    max_retries: int = 3
    request_timeout: int = 30
    rate_limit_delay: float = 1.0


class StateConfig(BaseModel):
    """Configuration for state management."""
    backend: str = "json"  # json or sqlite
    directory: Path = Path("./simulations")
    enable_checkpoints: bool = True
    max_history_size: int = 1000


class FrameworkConfig(BaseModel):
    """Main framework configuration."""
    
    # LLM Provider configurations
    openrouter: Optional[LLMProviderConfig] = None
    lm_studio: Optional[LLMProviderConfig] = None
    
    # State management
    state: StateConfig = Field(default_factory=StateConfig)
    
    # Logging and debugging
    log_level: str = "INFO"
    debug_mode: bool = False
    enable_metrics: bool = True
    
    # Simulation settings
    simulation_timeout: int = 300  # seconds
    max_conversation_length: int = 1000
    
    @classmethod
    def from_env(cls, env_file: Optional[str] = None) -> "FrameworkConfig":
        """Load configuration from environment variables."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()
        
        config_data: Dict[str, Any] = {}
        
        # OpenRouter configuration
        if os.getenv("OPENROUTER_API_KEY"):
            config_data["openrouter"] = LLMProviderConfig(
                api_key=os.getenv("OPENROUTER_API_KEY", ""),
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                default_model=os.getenv("DEFAULT_OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
                fallback_models=[
                    model.strip() 
                    for model in os.getenv("FALLBACK_OPENROUTER_MODEL", "").split(",")
                    if model.strip()
                ],
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
                rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
            )
        
        # LM Studio configuration
        lm_studio_url = os.getenv("LM_STUDIO_BASE_URL", "http://localhost:1234/v1")
        config_data["lm_studio"] = LLMProviderConfig(
            api_key=os.getenv("LM_STUDIO_API_KEY", "not-needed-for-local"),
            base_url=lm_studio_url,
            default_model=os.getenv("DEFAULT_LM_STUDIO_MODEL", "local-model"),
            fallback_models=[],
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            request_timeout=int(os.getenv("REQUEST_TIMEOUT", "30")),
            rate_limit_delay=float(os.getenv("RATE_LIMIT_DELAY", "1.0"))
        )
        
        # State configuration
        config_data["state"] = StateConfig(
            backend=os.getenv("STATE_BACKEND", "json"),
            directory=Path(os.getenv("STATE_DIRECTORY", "./simulations")),
            enable_checkpoints=os.getenv("ENABLE_STATE_CHECKPOINTS", "true").lower() == "true"
        )
        
        # Framework settings
        config_data.update({
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
            "enable_metrics": os.getenv("ENABLE_METRICS", "true").lower() == "true",
            "simulation_timeout": int(os.getenv("SIMULATION_TIMEOUT", "300")),
        })
        
        return cls(**config_data)
    
    def create_state_directory(self) -> None:
        """Ensure the state directory exists."""
        self.state.directory.mkdir(parents=True, exist_ok=True)
    
    def validate_llm_providers(self) -> bool:
        """Check if at least one LLM provider is configured."""
        return self.openrouter is not None or self.lm_studio is not None


# Global configuration instance
_config: Optional[FrameworkConfig] = None


def get_config() -> FrameworkConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = FrameworkConfig.from_env()
    return _config


def set_config(config: FrameworkConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config
    _config = None
