"""
Test configuration and fixtures for PyScrAI
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import create_database, drop_database, database_exists
from alembic.config import Config
from alembic import command

from pyscrai.databases.models.base import Base
from pyscrai.databases.database import DATABASE_URL

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Create test database engine and apply migrations"""
    db_url = "sqlite:///:memory:"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    alembic_cfg = Config("pyscrai/databases/alembic.ini")
    # Set the sqlalchemy.url in alembic_cfg. This is often used by env.py
    # to know where the database is, even if we provide a direct connection.
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    # Apply migrations using the engine's connection
    with engine.connect() as connection:
        # Pass the live connection to Alembic's context attributes
        alembic_cfg.attributes['connection'] = connection
        command.upgrade(alembic_cfg, "head")
        # The connection.commit() is usually handled by Alembic's migration context
        # or by the autocommit nature of DDL in some DBs.
        # For SQLite, changes are typically committed when the transaction within `command.upgrade` finishes.

    # Ensure all tables are created according to the models' metadata
    # This can catch any discrepancies or tables not handled by migrations
    Base.metadata.create_all(engine)

    return engine


@pytest.fixture(scope="function")
def test_db_session(engine):
    """Create a new database session for a test"""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
