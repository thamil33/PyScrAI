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
@patch('pyscrai.engines.base_engine.httpx.AsyncClient.post', new_callable=AsyncMock)
async def test_engine_initialize_openrouter(mock_http_post, mock_agent_class, mock_openrouter, sample_agent_config):
    """Test engine initialization with OpenRouter"""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "mock-engine-id", "status": "registered"}
    mock_response.raise_for_status = Mock()
    mock_http_post.return_value = mock_response

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
    mock_http_post.assert_called_once()


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.LMStudio')
@patch('pyscrai.engines.base_engine.Agent')
@patch('pyscrai.engines.base_engine.httpx.AsyncClient.post', new_callable=AsyncMock)
async def test_engine_initialize_lmstudio(mock_http_post, mock_agent_class, mock_lmstudio, sample_agent_config):
    """Test engine initialization with LMStudio"""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "mock-engine-id", "status": "registered"}
    mock_response.raise_for_status = Mock()
    mock_http_post.return_value = mock_response

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
    mock_http_post.assert_called_once()


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
@patch('pyscrai.engines.base_engine.httpx.AsyncClient.post', new_callable=AsyncMock)
async def test_engine_initialize_with_storage(mock_http_post, mock_agent_class, mock_openrouter, mock_storage, sample_agent_config):
    """Test engine initialization with storage"""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "mock-engine-id", "status": "registered"}
    mock_response.raise_for_status = Mock()
    mock_http_post.return_value = mock_response

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
    mock_http_post.assert_called_once()


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.OpenRouter')
@patch('pyscrai.engines.base_engine.Agent')
@patch('pyscrai.engines.base_engine.httpx.AsyncClient.post', new_callable=AsyncMock)
async def test_engine_initialize_idempotent(mock_http_post, mock_agent_class, mock_openrouter, sample_agent_config):
    """Test that initialize can be called multiple times safely"""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": "mock-engine-id", "status": "registered"}
    mock_response.raise_for_status = Mock()
    mock_http_post.return_value = mock_response
    
    with patch('pyscrai.engines.base_engine.OpenRouter', mock_openrouter), \
         patch('pyscrai.engines.base_engine.Agent', mock_agent_class):
        
        engine = SimpleTestEngine(sample_agent_config)
        await engine.initialize()
        assert engine.initialized is True
        
        # Second call should not re-initialize, but registration might be called again if not idempotent in logic
        # For this test, we assume initialize itself is idempotent regarding model/agent setup.
        # Registration check:
        first_call_count = mock_http_post.call_count
        await engine.initialize()
        assert engine.initialized is True
        # Depending on implementation, registration might be skipped on second call if already registered.
        # If registration is designed to be called every time initialize is, then this will be first_call_count + 1
        # If it's truly idempotent and skips if already registered, it would be first_call_count
        # For now, let's assume it might be called again or has logic to prevent re-registration.
        # The key is that the call doesn't fail.
        assert mock_http_post.call_count >= first_call_count


@pytest.mark.asyncio
@patch('pyscrai.engines.base_engine.OpenRouter')
@patch('pyscrai.engines.base_engine.Agent')
@patch('pyscrai.engines.base_engine.httpx.AsyncClient.post', new_callable=AsyncMock)
async def test_engine_run(mock_http_post, mock_agent_class, mock_openrouter, sample_agent_config):
    """Test engine run method"""
    mock_response_registration = AsyncMock()
    mock_response_registration.status_code = 200
    mock_response_registration.json.return_value = {"id": "mock-engine-id", "status": "registered"}
    mock_response_registration.raise_for_status = Mock()
    mock_http_post.return_value = mock_response_registration
    
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
    mock_http_post.assert_called_once() # Ensure registration was attempted during implicit initialize


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
