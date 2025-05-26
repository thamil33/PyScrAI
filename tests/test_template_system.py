"""
Tests for the generic template system and its integration with engines and factories.
"""

import pytest
from sqlalchemy.orm import Session
from pyscrai.factories import TemplateManager, AgentFactory, ScenarioFactory
from pyscrai.engines import NarratorEngine, AnalystEngine
from pyscrai.databases.models import ScenarioTemplate, AgentTemplate
from pyscrai.databases.models.schemas import ScenarioTemplateCreate, AgentTemplateCreate

@pytest.fixture
def test_db():
    """Fixture for providing a test database session."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from pyscrai.databases.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()

@pytest.fixture
def template_manager(test_db: Session):
    """Fixture for TemplateManager."""
    return TemplateManager(test_db)

@pytest.fixture
def agent_factory(test_db: Session):
    """Fixture for AgentFactory."""
    return AgentFactory(test_db)

@pytest.fixture
def scenario_factory(test_db: Session):
    """Fixture for ScenarioFactory."""
    return ScenarioFactory(test_db)


@pytest.fixture
def setup_agent_template(test_db: Session):
    """Fixture to create a required AgentTemplate for tests."""
    from pyscrai.databases.models import AgentTemplate

    agent_template = AgentTemplate(
        name="Test Agent",
        description="A test agent template.",
        personality_config={"trait": "helpful", "role": "assistant"},
        llm_config={"temperature": 0.7, "provider": "openai", "model_id": "gpt-3.5-turbo"},
        tools_config={"tool1": {"name": "Test Tool", "enabled": True}}
    )
    test_db.add(agent_template)
    test_db.commit()
    test_db.refresh(agent_template)
    return agent_template


def test_create_scenario_template(template_manager: TemplateManager):
    """Test creating a scenario template."""
    template_data = ScenarioTemplateCreate(
        name="Test Scenario",
        description="A test scenario template.",
        config={"max_turns": 5},
        agent_roles={"role1": {"template_name": "Test Agent"}},
        event_flow={"start": {"type": "trigger"}}
    )

    template = template_manager.create_scenario_template(template_data)
    assert template.name == "Test Scenario"
    assert template.description == "A test scenario template."


def test_create_agent_template(template_manager: TemplateManager):
    """Test creating an agent template."""
    template_data = AgentTemplateCreate(
        name="Test Agent",
        description="A test agent template.",
        personality_config={"trait": "helpful", "role": "assistant"},
        llm_config={"temperature": 0.7, "provider": "openai", "model_id": "gpt-3.5-turbo"},
        tools_config={"tool1": {"name": "Test Tool", "enabled": True}}
    )

    template = template_manager.create_agent_template(template_data)
    assert template.name == "Test Agent"
    assert template.description == "A test agent template."


def test_narrator_engine_with_template(template_manager: TemplateManager):
    """Test NarratorEngine initialization with a template."""
    template_data = AgentTemplateCreate(
        name="Narrator Template",
        description="Template for NarratorEngine.",
        personality_config={"narrative_style": "descriptive and engaging", "role": "narrator"},
        llm_config={"temperature": 0.5, "provider": "openai", "model_id": "gpt-3.5-turbo"},
        tools_config={}
    )

    template = template_manager.create_agent_template(template_data)
    engine = NarratorEngine(agent_config=template.personality_config)

    assert engine.narrative_style == "descriptive and engaging"


def test_analyst_engine_with_template(template_manager: TemplateManager):
    """Test AnalystEngine initialization with a template."""
    template_data = AgentTemplateCreate(
        name="Analyst Template",
        description="Template for AnalystEngine.",
        personality_config={"analysis_focus": "behavioral patterns", "role": "analyst"},
        llm_config={"temperature": 0.6, "provider": "openai", "model_id": "gpt-3.5-turbo"},
        tools_config={}
    )

    template = template_manager.create_agent_template(template_data)
    engine = AnalystEngine(agent_config=template.personality_config)

    assert engine.analysis_focus == "behavioral patterns"


def test_scenario_factory_with_template(scenario_factory: ScenarioFactory, setup_agent_template):
    """Test ScenarioFactory creating a scenario run from a template."""
    template_data = ScenarioTemplateCreate(
        name="Scenario Template",
        description="A test scenario template.",
        config={"max_turns": 10},
        agent_roles={"role1": {"template_name": "Test Agent"}},
        event_flow={"start": {"type": "trigger"}}
    )

    template = scenario_factory.template_manager.create_scenario_template(template_data)
    scenario_run = scenario_factory.create_scenario_run_from_template(
        template_name=template.name,
        run_name="Test Run"
    )

    assert scenario_run.name == "Test Run"
    assert scenario_run.template_id == template.id
