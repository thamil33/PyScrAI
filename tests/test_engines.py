"""
Tests for PyScrAI engines
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from pyscrai.engines.base_engine import BaseEngine


class SimpleTestEngine(BaseEngine):
    """Simple test engine for testing purposes"""
    
    def _setup_tools(self):
        """No tools for basic testing"""
        return []
    
    async def process(self, input_data):
        """Simple processing for testing"""
        message = input_data.get("message", "test message")
        return {"result": f"Processed: {message}"}


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing"""
    return {
        "name": "Test Agent",
        "description": "A test agent for testing purposes",
        "model": "test-model",
        "model_config": {
            "id": "test-model-id",
            "temperature": 0.5
        },
        "personality_config": {
            "name": "Test Agent",
            "description": "Test description",
            "instructions": "Test instructions"
        }
    }


def test_base_engine_creation(sample_agent_config):
    """Test that BaseEngine can be instantiated"""
    engine = SimpleTestEngine(sample_agent_config)
    assert engine is not None
    assert engine.agent_config == sample_agent_config
    assert engine.model_provider == "openrouter"
    assert engine.initialized is False
    assert engine.agent is None
    assert engine.state == {}


def test_base_engine_creation_with_params(sample_agent_config):
    """Test BaseEngine creation with custom parameters"""
    engine = SimpleTestEngine(
        sample_agent_config,
        storage_path="/test/path",
        model_provider="lmstudio"
    )
    assert engine.storage_path == "/test/path"
    assert engine.model_provider == "lmstudio"


@pytest.mark.asyncio
async def test_engine_process(sample_agent_config):
    """Test engine processing functionality"""
    engine = SimpleTestEngine(sample_agent_config)
    
    input_data = {"message": "Hello, World!"}
    result = await engine.process(input_data)
    
    assert result == {"result": "Processed: Hello, World!"}


@pytest.mark.asyncio
async def test_engine_process_default(sample_agent_config):
    """Test engine processing with default message"""
    engine = SimpleTestEngine(sample_agent_config)
    
    input_data = {}
    result = await engine.process(input_data)
    
    assert result == {"result": "Processed: test message"}


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.OpenRouter')
@patch('pyscrai.engines.base_engine.Agent')
async def test_engine_initialize_openrouter(mock_agent_class, mock_openrouter, sample_agent_config):
    """Test engine initialization with OpenRouter"""
    mock_model = Mock()
    mock_openrouter.return_value = mock_model
    mock_agent = Mock()
    mock_agent_class.return_value = mock_agent
    
    engine = SimpleTestEngine(sample_agent_config)
    await engine.initialize()
    
    assert engine.initialized is True
    assert engine.agent is mock_agent
    mock_openrouter.assert_called_once()
    mock_agent_class.assert_called_once()


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.LMStudio')
@patch('pyscrai.engines.base_engine.Agent')
async def test_engine_initialize_lmstudio(mock_agent_class, mock_lmstudio, sample_agent_config):
    """Test engine initialization with LMStudio"""
    mock_model = Mock()
    mock_lmstudio.return_value = mock_model
    mock_agent = Mock()
    mock_agent_class.return_value = mock_agent
    
    engine = SimpleTestEngine(sample_agent_config, model_provider="lmstudio")
    await engine.initialize()
    
    assert engine.initialized is True
    assert engine.agent is mock_agent
    mock_lmstudio.assert_called_once()
    mock_agent_class.assert_called_once()


@pytest.mark.asyncio
async def test_engine_initialize_invalid_provider(sample_agent_config):
    """Test engine initialization with invalid provider"""
    engine = SimpleTestEngine(sample_agent_config, model_provider="invalid")
    
    with pytest.raises(ValueError, match="Unsupported model provider"):
        await engine.initialize()


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.SqliteStorage')
@patch('pyscrai.engines.base_engine.OpenRouter')
@patch('pyscrai.engines.base_engine.Agent')
async def test_engine_initialize_with_storage(mock_agent_class, mock_openrouter, mock_storage, sample_agent_config):
    """Test engine initialization with storage"""
    mock_model = Mock()
    mock_openrouter.return_value = mock_model
    mock_agent = Mock()
    mock_agent_class.return_value = mock_agent
    mock_storage_instance = Mock()
    mock_storage.return_value = mock_storage_instance
    
    engine = SimpleTestEngine(sample_agent_config, storage_path="/test/path")
    await engine.initialize()
    
    assert engine.initialized is True
    mock_storage.assert_called_once_with(
        db_file="/test/path",
        table_name="engine_simpletestengine"
    )


@pytest.mark.asyncio
async def test_engine_initialize_idempotent(sample_agent_config):
    """Test that initialize can be called multiple times safely"""
    with patch('pyscrai.engines.base_engine.OpenRouter'), \
         patch('pyscrai.engines.base_engine.Agent'):
        
        engine = SimpleTestEngine(sample_agent_config)
        await engine.initialize()
        assert engine.initialized is True
        
        # Second call should not re-initialize
        await engine.initialize()
        assert engine.initialized is True


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.OpenRouter')
@patch('pyscrai.engines.base_engine.Agent')
async def test_engine_run(mock_agent_class, mock_openrouter, sample_agent_config):
    """Test engine run method"""
    # Mock the agent and its response
    mock_response = Mock()
    mock_response.content = "Test response"
    mock_response.messages = [Mock()]
    mock_response.messages[0].dict.return_value = {"role": "assistant", "content": "Test"}
    mock_response.metrics = Mock()
    mock_response.metrics.dict.return_value = {"tokens": 10}
    
    mock_agent = Mock()
    mock_agent.arun = AsyncMock(return_value=mock_response)
    mock_agent_class.return_value = mock_agent
    
    mock_model = Mock()
    mock_openrouter.return_value = mock_model
    
    engine = SimpleTestEngine(sample_agent_config)
    result = await engine.run("Test message")
    
    assert result["content"] == "Test response"
    assert result["engine_type"] == "SimpleTestEngine"
    assert "messages" in result
    assert "metrics" in result
    assert "state" in result
    mock_agent.arun.assert_called_once_with("Test message")


def test_engine_setup_tools_abstract():
    """Test that _setup_tools is abstract"""
    # This is implicitly tested by our SimpleTestEngine implementation
    engine = SimpleTestEngine({})
    tools = engine._setup_tools()
    assert tools == []


def test_engine_process_abstract():
    """Test that process is abstract in base class"""
    # Cannot instantiate BaseEngine directly due to abstract methods
    with pytest.raises(TypeError):
        BaseEngine({})


def test_engine_state_management(sample_agent_config):
    """Test engine state management"""
    engine = SimpleTestEngine(sample_agent_config)
    
    # Initial state should be empty
    assert engine.state == {}
    
    # Modify state
    engine.state["test_key"] = "test_value"
    assert engine.state["test_key"] == "test_value"
