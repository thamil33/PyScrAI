"""
Tests for database configuration and session management
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from pyscrai.databases.database import (
    DATABASE_URL, 
    engine, 
    SessionLocal, 
    get_db
)


def test_database_url():
    """Test that DATABASE_URL is correctly defined"""
    assert DATABASE_URL == "sqlite:///data/pyscrai.db"


def test_engine_creation():
    """Test that engine is created correctly"""
    assert engine is not None
    assert hasattr(engine, 'url')


def test_session_local_creation():
    """Test that SessionLocal is created correctly"""
    assert SessionLocal is not None
    # Check sessionmaker configuration
    assert not SessionLocal.kw.get('autocommit', True)  # Should be False
    assert not SessionLocal.kw.get('autoflush', True)   # Should be False
    assert SessionLocal.kw.get('bind') is engine


def test_get_db_generator():
    """Test get_db function returns a generator"""
    db_gen = get_db()
    assert hasattr(db_gen, '__iter__')
    assert hasattr(db_gen, '__next__')


def test_get_db_yields_session():
    """Test that get_db yields a Session instance"""
    with patch('pyscrai.databases.database.SessionLocal') as mock_session_local:
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        
        db_gen = get_db()
        session = next(db_gen)
        
        assert session is mock_session
        mock_session_local.assert_called_once()


def test_get_db_closes_session():
    """Test that get_db closes the session in finally block"""
    with patch('pyscrai.databases.database.SessionLocal') as mock_session_local:
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        
        db_gen = get_db()
        next(db_gen)
        
        # Simulate the generator being closed/garbage collected
        try:
            db_gen.close()
        except StopIteration:
            pass
        
        # Verify session was closed
        mock_session.close.assert_called_once()


def test_get_db_closes_session_on_exception():
    """Test that get_db closes the session even if an exception occurs"""
    with patch('pyscrai.databases.database.SessionLocal') as mock_session_local:
        mock_session = MagicMock(spec=Session)
        mock_session_local.return_value = mock_session
        
        db_gen = get_db()
        next(db_gen)
        
        # Simulate an exception by throwing into the generator
        try:
            db_gen.throw(Exception("Test exception"))
        except Exception:
            pass
        
        # Verify session was closed despite the exception
        mock_session.close.assert_called_once()


def test_get_db_integration_with_real_session(test_db: Session):
    """Integration test with real database session"""
    from sqlalchemy import text
    
    # Use the test database session to verify it works
    result = test_db.execute(text("SELECT 1")).scalar()
    assert result == 1
    
    # Test that get_db actually produces working sessions
    db_gen = get_db()
    session = next(db_gen)
    
    # This should work without errors
    assert session is not None
    assert hasattr(session, 'execute')
    
    # Clean up
    try:
        db_gen.close()
    except StopIteration:
        pass
