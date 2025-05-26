"""
Tests for PyScrAI engines
"""
import pytest

from pyscrai.engines.base_engine import BaseEngine


class SimpleTestEngine(BaseEngine):
    """Simple test engine for testing purposes"""
    
    def _setup_tools(self):
        """No tools for basic testing"""
        return []
    
    async def process(self, input_data):
        """Simple processing for testing"""
        message = input_data.get("message", "test message")
        return f"Processed: {message}"


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing"""
    return {
        "name": "Test Agent",
        "description": "A test agent for testing purposes",
        "model": "test-model"
    }


def test_base_engine_creation(sample_agent_config):
    """Test that BaseEngine can be instantiated"""
    engine = SimpleTestEngine(sample_agent_config)
    assert engine is not None
    assert engine.agent_config == sample_agent_config


@pytest.mark.asyncio
async def test_engine_process(sample_agent_config):
    """Test engine processing functionality"""
    engine = SimpleTestEngine(sample_agent_config)
    
    input_data = {"message": "Hello, World!"}
    result = await engine.process(input_data)
    
    assert result == "Processed: Hello, World!"


@pytest.mark.asyncio
async def test_engine_process_default(sample_agent_config):
    """Test engine processing with default message"""
    engine = SimpleTestEngine(sample_agent_config)
    
    result = await engine.process({})
    
    assert result == "Processed: test message"
