"""
Tests for PyScrAI factories
"""
import pytest
from sqlalchemy.orm import Session

from pyscrai.factories import TemplateManager


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
