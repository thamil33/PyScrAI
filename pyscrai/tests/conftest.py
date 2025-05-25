import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from PyScrAI.models import Base  # Adjust the import based on your actual models

@pytest.fixture(scope='session')
def db_engine():
    engine = create_engine('sqlite:///data/pyscrai.db')  # Adjust the database URL as needed
    yield engine
    engine.dispose()

@pytest.fixture(scope='session')
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(bind=connection)()

    Base.metadata.create_all(db_engine)  # Create tables

    yield session  # This is where the testing happens

    session.close()
    transaction.rollback()
    connection.close()