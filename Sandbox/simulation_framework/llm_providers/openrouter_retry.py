"""
OpenRouter API retry wrapper with fallback model support and circuit breaker pattern.

This module provides a robust wrapper around OpenRouter API calls with:
- Exponential backoff retry logic for rate limits and temporary failures
- Fallback model chains for graceful degradation
- Circuit breaker pattern to handle problematic models
- Comprehensive error classification and handling
"""

import asyncio
import logging
import random
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, AsyncIterator
from dataclasses import dataclass, field

import httpx
from openai import AsyncOpenAI
from pydantic import BaseModel

from .base_provider import (
    LLMProvider, LLMRequest, LLMResponse,
    LLMProviderError, LLMProviderConnectionError,
    LLMProviderAuthError, LLMProviderRateLimitError,
    LLMProviderModelError
)

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreakerState:
    """State tracking for circuit breaker pattern."""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    is_open: bool = False
    recovery_timeout: timedelta = field(default_factory=lambda: timedelta(minutes=5))


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter_max: float = 1.0
    circuit_breaker_threshold: int = 5


class OpenRouterRetryWrapper(LLMProvider):
    """
    Robust OpenRouter API wrapper with retry logic and fallback support.
    
    Features:
    - Exponential backoff retry for rate limits and temporary failures
    - Fallback model chains for graceful degradation
    - Circuit breaker pattern for problematic models
    - Comprehensive error handling and logging
    """
    
    def __init__(
        self,
        api_key: str,
        fallback_models: Optional[List[str]] = None,
        retry_config: Optional[RetryConfig] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        default_model: str = "openai/gpt-3.5-turbo"
    ):
        super().__init__(
            name="openrouter_retry",
            api_key=api_key,
            base_url=base_url,
            default_model=default_model
        )
        
        self.fallback_models = fallback_models or [
            "meta-llama/llama-3.1-8b-instruct:free",
            "microsoft/phi-3-mini-128k-instruct:free"
        ]
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breakers: Dict[str, CircuitBreakerState] = {}
        self.request_counts: Dict[str, int] = {}
        
        # Initialize OpenAI client for OpenRouter
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=httpx.Timeout(60.0)
        )
        
        logger.info(f"Initialized OpenRouter retry wrapper with {len(self.fallback_models)} fallback models")

    async def generate_with_fallback(self, prompt: str, primary_model: str) -> Tuple[str, str]:
        """
        Generate text with automatic fallback model support.
        
        Args:
            prompt: The input prompt
            primary_model: Primary model to try first
            
        Returns:
            Tuple of (response_text, actual_model_used)
        """
        request = LLMRequest(prompt=prompt, model=primary_model)
        response = await self.generate(request)
        return response.content, response.model_used

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate text with retry logic and fallback support."""
        models_to_try = [request.model or self.default_model] + self.fallback_models
        
        last_exception = None
        
        for model in models_to_try:
            # Check circuit breaker
            if self._is_circuit_breaker_open(model):
                logger.warning(f"Circuit breaker open for model {model}, skipping")
                continue
                
            try:
                return await self._generate_with_retry(request, model)
                
            except LLMProviderRateLimitError as e:
                logger.warning(f"Rate limit hit for model {model}: {e}")
                last_exception = e
                continue
                
            except LLMProviderModelError as e:
                logger.warning(f"Model error for {model}: {e}")
                self._record_circuit_breaker_failure(model)
                last_exception = e
                continue
                
            except LLMProviderAuthError as e:
                logger.error(f"Auth error for {model}: {e}")
                last_exception = e
                # Auth errors are permanent, don't try fallbacks
                break
                
            except Exception as e:
                logger.error(f"Unexpected error for model {model}: {e}")
                self._record_circuit_breaker_failure(model)
                last_exception = e
                continue
        
        # All models failed
        raise LLMProviderError(f"All models failed. Last error: {last_exception}")

    async def _generate_with_retry(self, request: LLMRequest, model: str) -> LLMResponse:
        """Generate text with retry logic for a specific model."""
        request_params = self._prepare_request(request)
        request_params["model"] = model
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                start_time = time.time()
                
                response = await self._client.chat.completions.create(**request_params)
                
                # Record successful request
                self._record_success(model)
                
                # Build response
                content = response.choices[0].message.content
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
                
                return LLMResponse(
                    content=content,
                    model_used=model,
                    usage=usage,
                    metadata={
                        "attempt": attempt + 1,
                        "duration": time.time() - start_time,
                        "response_id": response.id
                    },
                    provider=self.name,
                    request_id=response.id
                )
                
            except Exception as e:
                # Classify error
                is_retryable, delay = self._classify_error(e, attempt)
                
                if not is_retryable or attempt >= self.retry_config.max_retries:
                    self._record_circuit_breaker_failure(model)
                    self._raise_classified_error(e, model)
                
                # Wait before retry
                await asyncio.sleep(delay)
                logger.info(f"Retrying {model} after {delay:.2f}s (attempt {attempt + 1})")

    def _classify_error(self, error: Exception, attempt: int) -> Tuple[bool, float]:
        """
        Classify error and determine if retryable and delay.
        
        Returns:
            Tuple of (is_retryable, delay_seconds)
        """
        error_str = str(error).lower()
        
        # Rate limit errors - use recommended delay from headers
        if "429" in error_str or "rate limit" in error_str:
            delay = self._calculate_delay(attempt, base=30.0)  # Longer base for rate limits
            return True, delay
            
        # Temporary server errors
        if any(code in error_str for code in ["500", "502", "503", "504"]):
            delay = self._calculate_delay(attempt)
            return True, delay
            
        # Connection timeouts
        if any(term in error_str for term in ["timeout", "connection", "network"]):
            delay = self._calculate_delay(attempt)
            return True, delay
            
        # Free model quota exceeded - don't retry, fallback immediately
        if "quota" in error_str or "limit exceeded" in error_str:
            return False, 0.0
            
        # Authentication errors - permanent
        if any(term in error_str for term in ["401", "403", "unauthorized", "forbidden"]):
            return False, 0.0
            
        # Model not found - permanent
        if "404" in error_str or "not found" in error_str:
            return False, 0.0
            
        # Default: retry with standard delay
        delay = self._calculate_delay(attempt)
        return True, delay

    def _calculate_delay(self, attempt: int, base: Optional[float] = None) -> float:
        """Calculate exponential backoff delay with jitter."""
        base_delay = base or self.retry_config.base_delay
        
        # Exponential backoff
        delay = min(
            base_delay * (self.retry_config.exponential_base ** attempt),
            self.retry_config.max_delay
        )
        
        # Add jitter
        jitter = random.uniform(0, self.retry_config.jitter_max)
        return delay + jitter

    def _is_circuit_breaker_open(self, model: str) -> bool:
        """Check if circuit breaker is open for a model."""
        if model not in self.circuit_breakers:
            return False
            
        breaker = self.circuit_breakers[model]
        
        if not breaker.is_open:
            return False
            
        # Check if recovery timeout has passed
        if breaker.last_failure_time and \
           datetime.now() - breaker.last_failure_time > breaker.recovery_timeout:
            breaker.is_open = False
            breaker.failure_count = 0
            logger.info(f"Circuit breaker recovered for model {model}")
            return False
            
        return True

    def _record_circuit_breaker_failure(self, model: str):
        """Record a failure for circuit breaker tracking."""
        if model not in self.circuit_breakers:
            self.circuit_breakers[model] = CircuitBreakerState()
            
        breaker = self.circuit_breakers[model]
        breaker.failure_count += 1
        breaker.last_failure_time = datetime.now()
        
        if breaker.failure_count >= self.retry_config.circuit_breaker_threshold:
            breaker.is_open = True
            logger.warning(f"Circuit breaker opened for model {model} after {breaker.failure_count} failures")

    def _record_success(self, model: str):
        """Record a successful request."""
        if model in self.circuit_breakers:
            self.circuit_breakers[model].failure_count = 0
            
        self.request_counts[model] = self.request_counts.get(model, 0) + 1

    def _raise_classified_error(self, error: Exception, model: str):
        """Raise appropriately classified error."""
        error_str = str(error).lower()
        
        if "429" in error_str or "rate limit" in error_str:
            raise LLMProviderRateLimitError(f"Rate limit exceeded for {model}: {error}")
        elif any(term in error_str for term in ["401", "403", "unauthorized", "forbidden"]):
            raise LLMProviderAuthError(f"Authentication failed for {model}: {error}")
        elif "404" in error_str or "not found" in error_str:
            raise LLMProviderModelError(f"Model not found {model}: {error}")
        elif any(term in error_str for term in ["timeout", "connection", "network"]):
            raise LLMProviderConnectionError(f"Connection error for {model}: {error}")
        else:
            raise LLMProviderError(f"Error with {model}: {error}")

    async def generate_streaming(self, request: LLMRequest) -> AsyncIterator[str]:
        """Generate streaming response with fallback support."""
        models_to_try = [request.model or self.default_model] + self.fallback_models
        
        for model in models_to_try:
            if self._is_circuit_breaker_open(model):
                continue
                
            try:
                async for chunk in self._generate_streaming_with_retry(request, model):
                    yield chunk
                return
                
            except Exception as e:
                logger.warning(f"Streaming failed for {model}: {e}")
                self._record_circuit_breaker_failure(model)
                continue
                
        raise LLMProviderError("All models failed for streaming")

    async def _generate_streaming_with_retry(self, request: LLMRequest, model: str) -> AsyncIterator[str]:
        """Generate streaming response with retry logic."""
        request_params = self._prepare_request(request)
        request_params["model"] = model
        request_params["stream"] = True
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                stream = await self._client.chat.completions.create(**request_params)
                
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                        
                self._record_success(model)
                return
                
            except Exception as e:
                is_retryable, delay = self._classify_error(e, attempt)
                
                if not is_retryable or attempt >= self.retry_config.max_retries:
                    self._raise_classified_error(e, model)
                
                await asyncio.sleep(delay)

    async def get_embeddings(self, texts: List[str], model: Optional[str] = None) -> List[List[float]]:
        """Get embeddings with retry logic."""
        embedding_model = model or "text-embedding-ada-002"
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                response = await self._client.embeddings.create(
                    input=texts,
                    model=embedding_model
                )
                
                return [embedding.embedding for embedding in response.data]
                
            except Exception as e:
                is_retryable, delay = self._classify_error(e, attempt)
                
                if not is_retryable or attempt >= self.retry_config.max_retries:
                    self._raise_classified_error(e, embedding_model)
                
                await asyncio.sleep(delay)

    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models."""
        try:
            response = await self._client.models.list()
            return [{"id": model.id, "object": model.object} for model in response.data]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            raise LLMProviderConnectionError(f"Failed to list models: {e}") from e

    async def health_check(self) -> bool:
        """Check provider health."""
        try:
            await self.list_models()
            return True
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get wrapper statistics."""
        return {
            "request_counts": dict(self.request_counts),
            "circuit_breakers": {
                model: {
                    "failure_count": breaker.failure_count,
                    "is_open": breaker.is_open,
                    "last_failure": breaker.last_failure_time.isoformat() if breaker.last_failure_time else None
                }
                for model, breaker in self.circuit_breakers.items()
            },
            "fallback_models": self.fallback_models
        }
