"""
Base LLM interface for PyScrAI.
Provides a unified interface for different LLM providers without external dependencies.
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
import httpx

logger = logging.getLogger(__name__)


class BaseLLM(ABC):
    """
    Abstract base class for all LLM providers in PyScrAI.
    Provides a unified interface for different LLM services.
    """
    
    def __init__(
        self,
        model_id: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize the LLM instance.
        
        Args:
            model_id: The model identifier
            api_key: API key for authentication
            base_url: Base URL for the API
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
        """
        self.model_id = model_id
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.extra_params = kwargs
        
        # HTTP client for API calls
        self.client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"Initialized {self.__class__.__name__} with model {model_id}")
    
    async def _ensure_client(self):
        """Ensure HTTP client is initialized."""
        if self.client is None:
            headers = self._get_headers()
            self.client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0
            )
    
    async def _close_client(self):
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    @abstractmethod
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        pass
    
    @abstractmethod
    def _format_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Format the request payload for the specific provider."""
        pass
    
    @abstractmethod
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Extract the generated text from the provider's response."""
        pass
    
    async def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a prompt (synchronous-style interface).
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text string
        """
        return await self.agenerate(prompt, **kwargs)
    
    async def agenerate(self, prompt: str, **kwargs) -> str:
        """
        Generate text from a prompt (async interface).
        
        Args:
            prompt: The input prompt
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text string
        """
        try:
            await self._ensure_client()
            
            # Format request
            request_data = self._format_request(prompt, **kwargs)
            
            # Make API call
            response = await self.client.post(
                self._get_endpoint(),
                json=request_data
            )
            response.raise_for_status()
            
            # Extract and return response
            response_data = response.json()
            return self._extract_response(response_data)
            
        except Exception as e:
            logger.error(f"Error generating text with {self.__class__.__name__}: {e}")
            raise
    
    @abstractmethod
    def _get_endpoint(self) -> str:
        """Get the API endpoint for text generation."""
        pass
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_client()


class OpenRouterLLM(BaseLLM):
    """OpenRouter LLM implementation."""
    
    def __init__(
        self,
        model_id: str,
        api_key: str,
        base_url: str = "https://openrouter.ai/api/v1",
        site_url: Optional[str] = None,
        app_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_id, api_key, base_url, **kwargs)
        self.site_url = site_url
        self.app_name = app_name
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for OpenRouter API requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        
        if self.app_name:
            headers["X-Title"] = self.app_name
        
        return headers
    
    def _format_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Format request for OpenRouter API."""
        # Merge instance params with call-time params
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        request_data = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        # Add any extra parameters
        for key, value in self.extra_params.items():
            if key not in request_data:
                request_data[key] = value
        
        return request_data
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Extract response from OpenRouter API response."""
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response from OpenRouter: {e}")
            logger.debug(f"Response data: {response_data}")
            raise ValueError("Invalid response format from OpenRouter")
    
    def _get_endpoint(self) -> str:
        """Get OpenRouter chat completions endpoint."""
        return "/chat/completions"


class LMStudioLLM(BaseLLM):
    """LMStudio local LLM implementation."""
    
    def __init__(
        self,
        model_id: str,
        base_url: str = "http://localhost:1234/v1",
        api_key: Optional[str] = None,
        **kwargs
    ):
        super().__init__(model_id, api_key, base_url, **kwargs)
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for LMStudio API requests."""
        headers = {"Content-Type": "application/json"}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        return headers
    
    def _format_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Format request for LMStudio API."""
        temperature = kwargs.get("temperature", self.temperature)
        max_tokens = kwargs.get("max_tokens", self.max_tokens)
        
        request_data = {
            "model": self.model_id,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature
        }
        
        if max_tokens:
            request_data["max_tokens"] = max_tokens
        
        return request_data
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Extract response from LMStudio API response."""
        try:
            return response_data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to extract response from LMStudio: {e}")
            logger.debug(f"Response data: {response_data}")
            raise ValueError("Invalid response format from LMStudio")
    
    def _get_endpoint(self) -> str:
        """Get LMStudio chat completions endpoint."""
        return "/chat/completions"


class MockLLM(BaseLLM):
    """Mock LLM for testing and fallback scenarios."""
    
    def __init__(self, model_id: str = "mock-model", **kwargs):
        super().__init__(model_id, **kwargs)
    
    def _get_headers(self) -> Dict[str, str]:
        """Mock headers."""
        return {"Content-Type": "application/json"}
    
    def _format_request(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock request format."""
        return {"prompt": prompt}
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Mock response extraction."""
        return response_data.get("response", "Mock response")
    
    def _get_endpoint(self) -> str:
        """Mock endpoint."""
        return "/mock"
    
    async def agenerate(self, prompt: str, **kwargs) -> str:
        """Generate mock response without making HTTP calls."""
        # Simulate some processing time
        await asyncio.sleep(0.1)
        
        # Generate a simple mock response based on the prompt
        response = f"Mock LLM Response: I received the prompt '{prompt[:50]}...' and would provide an appropriate response based on the context."
        
        logger.debug(f"MockLLM generated: {response}")
        return response
