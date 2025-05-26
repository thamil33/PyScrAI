"""
Tests for PyScrAI factories
"""
import pytest
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from pyscrai.factories import TemplateManager, AgentFactory, ScenarioFactory


def test_template_manager_creation(test_db: Session):
    """Test that TemplateManager can be created"""
    manager = TemplateManager(test_db)
    assert manager is not None


def test_template_manager_list_templates(test_db: Session):
    """Test that TemplateManager can list templates"""
    manager = TemplateManager(test_db)
    
    # These should return empty lists initially but not fail
    agent_templates = manager.list_agent_templates()
    scenario_templates = manager.list_scenario_templates()
    
    assert isinstance(agent_templates, list)
    assert isinstance(scenario_templates, list)


def test_agent_factory_creation(test_db: Session):
    """Test that AgentFactory can be created"""
    factory = AgentFactory(test_db)
    assert factory is not None
    assert factory.db is test_db


def test_scenario_factory_creation(test_db: Session):
    """Test that ScenarioFactory can be created"""
    factory = ScenarioFactory(test_db)
    assert factory is not None
    assert factory.db is test_db
    assert isinstance(factory.agent_factory, AgentFactory)


def test_agent_factory_create_agent_instance_handles_missing_template(test_db: Session):
    """Test AgentFactory.create_agent_instance raises if template not found"""
    factory = AgentFactory(test_db)
    # Patch db.query to return None for template
    factory.db.query = MagicMock()
    factory.db.query().filter().first.side_effect = [None, None]
    with pytest.raises(ValueError, match="Agent template with ID 1 not found"):
        factory.create_agent_instance(1, 1, "Test Instance")


def test_agent_factory_create_agent_instance_handles_missing_scenario_run(test_db: Session):
    """Test AgentFactory.create_agent_instance raises if scenario run not found"""
    factory = AgentFactory(test_db)
    # Patch db.query to return a mock for template, None for scenario_run
    mock_template = MagicMock()
    factory.db.query = MagicMock()
    factory.db.query().filter().first.side_effect = [mock_template, None]
    with pytest.raises(ValueError, match="Scenario run with ID 1 not found"):
        factory.create_agent_instance(1, 1, "Test Instance")


def test_scenario_factory_create_scenario_run_handles_missing_template(test_db: Session):
    """Test ScenarioFactory.create_scenario_run raises if template not found"""
    factory = ScenarioFactory(test_db)
    factory.db.query = MagicMock()
    factory.db.query().filter().first.return_value = None
    with pytest.raises(ValueError, match="Scenario template with ID 1 not found"):
        factory.create_scenario_run(1, "Test Run")
