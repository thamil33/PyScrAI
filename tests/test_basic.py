"""
Basic tests for PyScrAI core functionality
"""
import pytest
from sqlalchemy.orm import Session

from pyscrai import __version__
from pyscrai.utils.config import Config


def test_version():
    """Test that version is defined"""
    assert __version__ == "0.1.0"


def test_config():
    """Test that config can be loaded"""
    config = Config()
    assert config is not None


def test_database_session(test_db: Session):
    """Test that database session is working"""
    from sqlalchemy import text
    
    assert test_db is not None
    # Test a simple query to ensure the session works
    result = test_db.execute(text("SELECT 1")).scalar()
    assert result == 1
