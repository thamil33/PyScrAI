"""
Tests for OpenRouter retry wrapper functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from simulation_framework.llm_providers import (
    OpenRouterRetryWrapper, RetryConfig, CircuitBreakerState
)
from simulation_framework.llm_providers.base_provider import (
    LLMRequest, LLMResponse, LLMProviderRateLimitError,
    LLMProviderModelError, LLMProviderAuthError
)


@pytest.fixture
def retry_wrapper():
    """Create a test retry wrapper instance."""
    return OpenRouterRetryWrapper(
        api_key="test-key",
        fallback_models=["test-fallback-1", "test-fallback-2"],
        retry_config=RetryConfig(max_retries=2, base_delay=0.1, max_delay=1.0)
    )


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    client = AsyncMock()
    return client


class TestOpenRouterRetryWrapper:
    """Test cases for OpenRouter retry wrapper."""

    @pytest.mark.asyncio
    async def test_successful_generation(self, retry_wrapper, mock_openai_client):
        """Test successful text generation without retries."""
        # Mock successful response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.id = "test-id"
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        retry_wrapper._client = mock_openai_client
        
        request = LLMRequest(prompt="Test prompt", model="test-model")
        response = await retry_wrapper.generate(request)
        
        assert response.content == "Test response"
        assert response.model_used == "test-model"
        assert response.usage["total_tokens"] == 30
        assert mock_openai_client.chat.completions.create.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, retry_wrapper, mock_openai_client):
        """Test retry logic for rate limit errors."""
        # First call fails with rate limit, second succeeds
        mock_openai_client.chat.completions.create.side_effect = [
            Exception("429 Rate limit exceeded"),
            Mock(
                choices=[Mock(message=Mock(content="Success"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                id="test-id"
            )
        ]
        retry_wrapper._client = mock_openai_client
        
        request = LLMRequest(prompt="Test prompt", model="test-model")
        response = await retry_wrapper.generate(request)
        
        assert response.content == "Success"
        assert mock_openai_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_on_model_error(self, retry_wrapper, mock_openai_client):
        """Test fallback to alternative models on model errors."""
        # Primary model fails, fallback succeeds
        mock_openai_client.chat.completions.create.side_effect = [
            Exception("404 Model not found"),  # Primary model fails
            Mock(
                choices=[Mock(message=Mock(content="Fallback success"))],
                usage=Mock(prompt_tokens=10, completion_tokens=20, total_tokens=30),
                id="fallback-id"
            )
        ]
        retry_wrapper._client = mock_openai_client
        
        request = LLMRequest(prompt="Test prompt", model="primary-model")
        response = await retry_wrapper.generate(request)
        
        assert response.content == "Fallback success"
        assert response.model_used == "test-fallback-1"  # First fallback model
        assert mock_openai_client.chat.completions.create.call_count == 2

    @pytest.mark.asyncio
    async def test_circuit_breaker_opens(self, retry_wrapper, mock_openai_client):
        """Test circuit breaker opens after repeated failures."""
        # Simulate repeated failures to trigger circuit breaker
        mock_openai_client.chat.completions.create.side_effect = Exception("500 Server error")
        retry_wrapper._client = mock_openai_client
        
        # Make multiple failed requests to trigger circuit breaker
        for _ in range(retry_wrapper.retry_config.circuit_breaker_threshold):
            try:
                request = LLMRequest(prompt="Test prompt", model="failing-model")
                await retry_wrapper.generate(request)
            except Exception:
                pass  # Expected to fail
        
        # Circuit breaker should now be open for the failing model
        assert retry_wrapper._is_circuit_breaker_open("failing-model")
        assert retry_wrapper.circuit_breakers["failing-model"].is_open

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self, retry_wrapper):
        """Test circuit breaker recovery after timeout."""
        # Manually set circuit breaker state
        breaker = CircuitBreakerState(
            failure_count=10,
            is_open=True,
            last_failure_time=datetime.now() - timedelta(minutes=10),  # Past recovery timeout
            recovery_timeout=timedelta(minutes=5)
        )
        retry_wrapper.circuit_breakers["test-model"] = breaker
        
        # Circuit breaker should recover
        assert not retry_wrapper._is_circuit_breaker_open("test-model")
        assert not breaker.is_open
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_generate_with_fallback_method(self, retry_wrapper, mock_openai_client):
        """Test the generate_with_fallback convenience method."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.id = "test-id"
        
        mock_openai_client.chat.completions.create.return_value = mock_response
        retry_wrapper._client = mock_openai_client
        
        response_text, model_used = await retry_wrapper.generate_with_fallback(
            "Test prompt", "test-model"
        )
        
        assert response_text == "Test response"
        assert model_used == "test-model"

    def test_error_classification(self, retry_wrapper):
        """Test error classification logic."""
        # Rate limit error - should retry
        is_retryable, delay = retry_wrapper._classify_error(Exception("429 Rate limit"), 0)
        assert is_retryable
        assert delay > 0
        
        # Auth error - should not retry
        is_retryable, delay = retry_wrapper._classify_error(Exception("401 Unauthorized"), 0)
        assert not is_retryable
        
        # Model not found - should not retry
        is_retryable, delay = retry_wrapper._classify_error(Exception("404 Not found"), 0)
        assert not is_retryable
        
        # Quota exceeded - should not retry (immediate fallback)
        is_retryable, delay = retry_wrapper._classify_error(Exception("Quota exceeded"), 0)
        assert not is_retryable
        
        # Server error - should retry
        is_retryable, delay = retry_wrapper._classify_error(Exception("500 Server error"), 0)
        assert is_retryable

    def test_delay_calculation(self, retry_wrapper):
        """Test exponential backoff delay calculation."""
        # Test exponential growth
        delay_0 = retry_wrapper._calculate_delay(0)
        delay_1 = retry_wrapper._calculate_delay(1)
        delay_2 = retry_wrapper._calculate_delay(2)
        
        # Should grow exponentially (accounting for jitter)
        assert delay_1 > delay_0
        assert delay_2 > delay_1
        
        # Should respect max delay
        large_delay = retry_wrapper._calculate_delay(10)
        assert large_delay <= retry_wrapper.retry_config.max_delay + retry_wrapper.retry_config.jitter_max

    def test_stats_collection(self, retry_wrapper):
        """Test statistics collection."""
        # Record some stats
        retry_wrapper._record_success("test-model")
        retry_wrapper._record_circuit_breaker_failure("failing-model")
        
        stats = retry_wrapper.get_stats()
        
        assert "request_counts" in stats
        assert "circuit_breakers" in stats
        assert "fallback_models" in stats
        assert stats["request_counts"]["test-model"] == 1
        assert stats["circuit_breakers"]["failing-model"]["failure_count"] == 1

    @pytest.mark.asyncio
    async def test_health_check(self, retry_wrapper, mock_openai_client):
        """Test health check functionality."""
        mock_openai_client.models.list.return_value = Mock(data=[])
        retry_wrapper._client = mock_openai_client
        
        health = await retry_wrapper.health_check()
        assert health is True
        
        # Test failure case
        mock_openai_client.models.list.side_effect = Exception("Connection failed")
        health = await retry_wrapper.health_check()
        assert health is False
