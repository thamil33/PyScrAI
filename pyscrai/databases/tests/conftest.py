"""
Test configuration and fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import create_database, drop_database, database_exists

from pyscrai.databases.models.base import Base
from pyscrai.databases.database import DATABASE_URL

TEST_DATABASE_URL = f"{DATABASE_URL}_test"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    if database_exists(TEST_DATABASE_URL):
        drop_database(TEST_DATABASE_URL)
    
    create_database(TEST_DATABASE_URL)
    engine = create_engine(TEST_DATABASE_URL)
    
    Base.metadata.create_all(engine)
    
    yield engine
    
    drop_database(TEST_DATABASE_URL)


@pytest.fixture(scope="function")
def test_db_session(engine) -> Session:
    """Create a new database session for a test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
