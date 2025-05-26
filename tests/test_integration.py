"""
Integration tests for PyScrAI components working together
"""
import pytest
from sqlalchemy.orm import Session

from pyscrai.factories import TemplateManager, AgentFactory


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing"""
    return {
        "name": "Test Agent",
        "description": "A test agent for integration testing",
        "model": "test-model",
        "system_prompt": "You are a helpful test assistant."
    }


def test_template_manager_and_agent_factory_integration(test_db: Session, sample_agent_config):
    """Test that TemplateManager and AgentFactory can work together"""
    # Create template manager
    template_manager = TemplateManager(test_db)
    assert template_manager is not None
    
    # Create agent factory
    agent_factory = AgentFactory(test_db)
    assert agent_factory is not None
    
    # Both should work without errors
    agent_templates = template_manager.list_agent_templates()
    assert isinstance(agent_templates, list)


def test_complete_pyscrai_import():
    """Test that all main PyScrAI components can be imported"""
    from pyscrai import __version__, TemplateManager, AgentFactory, ScenarioFactory, BaseEngine, Config
    
    assert __version__ is not None
    assert TemplateManager is not None
    assert AgentFactory is not None
    assert ScenarioFactory is not None
    assert BaseEngine is not None
    assert Config is not None
