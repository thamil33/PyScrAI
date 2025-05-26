"""
Tests for LLM Factory functionality
"""
import pytest
from unittest.mock import patch, MagicMock
from pyscrai.factories.llm_factory import get_agno_llm_instance


@patch('pyscrai.factories.llm_factory.settings')
@patch('pyscrai.factories.llm_factory.AgnoOpenRouter')
def test_get_agno_llm_instance_openrouter_default(mock_openrouter, mock_settings):
    """Test getting OpenRouter instance with default settings"""
    # Mock settings
    mock_settings.PYSCRAI_DEFAULT_PROVIDER = "openrouter"
    mock_settings.PYSCRAI_OPENROUTER_MODEL_ID = "test-model"
    mock_settings.PYSCRAI_OPENROUTER_API_KEY = "test-key"
    
    # Mock OpenRouter instance
    mock_instance = MagicMock()
    mock_openrouter.return_value = mock_instance
    
    result = get_agno_llm_instance()
    
    assert result is mock_instance
    mock_openrouter.assert_called_once()


@patch('pyscrai.factories.llm_factory.settings')
@patch('pyscrai.factories.llm_factory.AgnoLMStudio')
def test_get_agno_llm_instance_lmstudio_default(mock_lmstudio, mock_settings):
    """Test getting LMStudio instance with default settings"""
    # Mock settings
    mock_settings.PYSCRAI_DEFAULT_PROVIDER = "lmstudio"
    mock_settings.PYSCRAI_LMSTUDIO_MODEL_ID = "test-model"
    mock_settings.PYSCRAI_LMSTUDIO_API_BASE = "http://localhost:1234"
    
    # Mock LMStudio instance
    mock_instance = MagicMock()
    mock_lmstudio.return_value = mock_instance
    
    result = get_agno_llm_instance()
    
    assert result is mock_instance
    mock_lmstudio.assert_called_once()


@patch('pyscrai.factories.llm_factory.settings')
@patch('pyscrai.factories.llm_factory.AgnoOpenRouter')
def test_get_agno_llm_instance_openrouter_override(mock_openrouter, mock_settings):
    """Test getting OpenRouter instance with provider override"""
    # Mock settings
    mock_settings.PYSCRAI_OPENROUTER_MODEL_ID = "default-model"
    mock_settings.PYSCRAI_OPENROUTER_API_KEY = "test-key"
    
    # Mock OpenRouter instance
    mock_instance = MagicMock()
    mock_openrouter.return_value = mock_instance
    
    result = get_agno_llm_instance(provider="openrouter", model_id="custom-model")
    
    assert result is mock_instance
    mock_openrouter.assert_called_once()


@patch('pyscrai.factories.llm_factory.settings')
@patch('pyscrai.factories.llm_factory.AgnoLMStudio')
def test_get_agno_llm_instance_lmstudio_override(mock_lmstudio, mock_settings):
    """Test getting LMStudio instance with provider override"""
    # Mock settings
    mock_settings.PYSCRAI_LMSTUDIO_MODEL_ID = "default-model"
    mock_settings.PYSCRAI_LMSTUDIO_API_BASE = "http://localhost:1234"
    
    # Mock LMStudio instance
    mock_instance = MagicMock()
    mock_lmstudio.return_value = mock_instance
    
    result = get_agno_llm_instance(provider="lmstudio", model_id="custom-model")
    
    assert result is mock_instance
    mock_lmstudio.assert_called_once()


@patch('pyscrai.factories.llm_factory.settings')
def test_get_agno_llm_instance_invalid_provider(mock_settings):
    """Test handling of invalid provider"""
    # Mock settings
    mock_settings.PYSCRAI_DEFAULT_PROVIDER = "invalid_provider"
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_agno_llm_instance()


@patch('pyscrai.factories.llm_factory.settings')
@patch('pyscrai.factories.llm_factory.AgnoOpenRouter')
def test_get_agno_llm_instance_with_kwargs(mock_openrouter, mock_settings):
    """Test passing additional kwargs to LLM instance"""
    # Mock settings
    mock_settings.PYSCRAI_DEFAULT_PROVIDER = "openrouter"
    mock_settings.PYSCRAI_OPENROUTER_MODEL_ID = "test-model"
    mock_settings.PYSCRAI_OPENROUTER_API_KEY = "test-key"
    
    # Mock OpenRouter instance
    mock_instance = MagicMock()
    mock_openrouter.return_value = mock_instance
    
    kwargs = {"temperature": 0.7, "max_tokens": 1000}
    result = get_agno_llm_instance(**kwargs)
    
    assert result is mock_instance
    # Verify kwargs were passed to the constructor
    call_args = mock_openrouter.call_args
    assert call_args is not None


def test_settings_import():
    """Test that settings can be imported"""
    from pyscrai.factories.llm_factory import settings
    assert settings is not None


def test_agno_imports():
    """Test that Agno model classes can be imported"""
    from pyscrai.factories.llm_factory import AgnoOpenRouter, AgnoLMStudio
    assert AgnoOpenRouter is not None
    assert AgnoLMStudio is not None
