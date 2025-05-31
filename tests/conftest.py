# PyScrAI Test Configuration and Fixtures
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Iterator # Added import

from pyscrai.databases.models import Base # Assuming your SQLAlchemy models inherit from this Base
from pyscrai.engines.scenario_runner import ScenarioRunner
from pyscrai.engines.orchestration.engine_manager import EngineManager
from pyscrai.factories.scenario_factory import ScenarioFactory
from pyscrai.factories.agent_factory import AgentFactory

# In-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def engine():
    """SQLAlchemy engine fixture, created once per session."""
    return create_engine(DATABASE_URL)

@pytest.fixture(scope="session", autouse=True)
def setup_database(engine):
    """Create database tables once per session."""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session(engine) -> Iterator[Session]: # Changed Session to Iterator[Session]
    """Database session fixture, created for each test function."""
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Bind an ORM session to the connection
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    # Rollback the transaction to ensure a clean state for the next test
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def agent_factory(db_session: Session) -> AgentFactory:
    """Fixture for AgentFactory."""
    return AgentFactory(db_session)

@pytest.fixture(scope="function")
def scenario_factory(db_session: Session) -> ScenarioFactory: # Removed agent_factory from parameters
    """Fixture for ScenarioFactory."""
    # ScenarioFactory initializes its own AgentFactory and TemplateManager.
    return ScenarioFactory(db_session)

@pytest.fixture(scope="function")
def engine_manager(db_session: Session) -> EngineManager:
    """Fixture for EngineManager."""
    return EngineManager(db=db_session, storage_base_path="./test_engine_manager_storage")

@pytest.fixture(scope="function")
def scenario_runner(db_session: Session, engine_manager: EngineManager, scenario_factory: ScenarioFactory) -> ScenarioRunner:
    """Fixture for ScenarioRunner."""
    runner = ScenarioRunner(db=db_session, storage_base_path="./test_scenario_storage")
    # Replace the default engine_manager and scenario_factory with our test fixtures
    runner.engine_manager = engine_manager
    runner.scenario_factory = scenario_factory
    return runner
