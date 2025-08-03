"""
Base LLM provider abstraction for the simulation framework.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, AsyncIterator
from pydantic import BaseModel
import asyncio


class LLMResponse(BaseModel):
    """Response from an LLM provider."""
    content: str
    model_used: str
    usage: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = {}
    provider: str
    request_id: Optional[str] = None


class LLMRequest(BaseModel):
    """Request to an LLM provider."""
    prompt: str
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    stop_sequences: List[str] = []
    metadata: Dict[str, Any] = {}


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    Supports both OpenRouter (cloud) and LM Studio (local) through
    OpenAI-compatible APIs.
    """
    
    def __init__(self, name: str, api_key: str, base_url: str, default_model: str):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url
        self.default_model = default_model
        self._client = None
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate text using the LLM.
        
        Args:
            request: The LLM request containing prompt and parameters
            
        Returns:
            LLM response with generated content and metadata
        """
        pass
    
    @abstractmethod
    async def generate_streaming(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Generate text using streaming response.
        
        Args:
            request: The LLM request containing prompt and parameters
            
        Yields:
            Chunks of generated text
        """
        pass
    
    @abstractmethod
    async def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """
        Generate embeddings for the given texts.
        
        Args:
            texts: List of texts to embed
            model: Optional model name for embeddings
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models for this provider.
        
        Returns:
            List of model information dictionaries
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and responsive.
        
        Returns:
            True if healthy, False otherwise
        """
        pass
    
    async def validate_model(self, model: str) -> bool:
        """
        Validate that a model is available.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is available, False otherwise
        """
        try:
            models = await self.list_models()
            available_models = [m.get('id', '') for m in models]
            return model in available_models
        except Exception:
            return False
    
    def _prepare_request(self, request: LLMRequest) -> Dict[str, Any]:
        """
        Prepare request parameters for the API call.
        
        Args:
            request: The LLM request
            
        Returns:
            Dictionary of API parameters
        """
        params = {
            "model": request.model or self.default_model,
            "messages": [],
            "temperature": request.temperature,
            "stream": False
        }
        
        if request.max_tokens:
            params["max_tokens"] = request.max_tokens
        
        if request.stop_sequences:
            params["stop"] = request.stop_sequences
        
        # Build messages array
        if request.system_prompt:
            params["messages"].append({
                "role": "system",
                "content": request.system_prompt
            })
        
        params["messages"].append({
            "role": "user", 
            "content": request.prompt
        })
        
        return params
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client and hasattr(self._client, 'close'):
            await self._client.close()


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""
    pass


class LLMProviderConnectionError(LLMProviderError):
    """Connection-related errors."""
    pass


class LLMProviderAuthError(LLMProviderError):
    """Authentication-related errors."""
    pass


class LLMProviderRateLimitError(LLMProviderError):
    """Rate limiting errors."""
    pass


class LLMProviderModelError(LLMProviderError):
    """Model-related errors."""
    pass
