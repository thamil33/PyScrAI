"""
Database configuration and session management for PyScrAI Universal Templates and Custom Engines
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine
from pathlib import Path
from typing import Generator
import sqlite3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "pyscrai.db"

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with optimized settings for our use case
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

# Enable foreign key constraints for SQLite
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # Better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Better performance
        cursor.execute("PRAGMA cache_size=10000")  # Larger cache
        cursor.execute("PRAGMA temp_store=MEMORY")  # Use memory for temp tables
        cursor.close()

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting database session in FastAPI endpoints
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Get a database session for direct usage (non-FastAPI contexts)
    
    Returns:
        Session: SQLAlchemy database session
        
    Note:
        Remember to close the session when done: session.close()
    """
    return SessionLocal()


def init_database():
    """
    Initialize the database with all tables for the universal template system
    """
    from .models import Base
    
    logger.info(f"Initializing PyScrAI database at: {DB_PATH}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
        
        # Seed initial data if needed
        _seed_initial_data()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def _seed_initial_data():
    """
    Seed the database with initial data required for the universal template system
    """
    from .models import EventType
    
    db = get_db_session()
    try:
        # Check if we already have event types
        existing_events = db.query(EventType).count()
        if existing_events > 0:
            logger.info("Database already contains initial data, skipping seed")
            return
        
        # Seed basic event types for universal templates
        basic_event_types = [
            {
                "name": "agent_message",
                "description": "Message sent by an agent",
                "event_category": "interaction",
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "recipient": {"type": "string"},
                        "message_type": {"type": "string"}
                    },
                    "required": ["content"]
                }
            },
            {
                "name": "system_notification",
                "description": "System-level notification",
                "event_category": "system",
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "notification_type": {"type": "string"},
                        "message": {"type": "string"},
                        "severity": {"type": "string"}
                    },
                    "required": ["notification_type", "message"]
                }
            },
            {
                "name": "narrative_event",
                "description": "Narrative progression event",
                "event_category": "narrative",
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "narrative_type": {"type": "string"},
                        "description": {"type": "string"},
                        "impact": {"type": "object"}
                    },
                    "required": ["narrative_type", "description"]
                }
            },
            {
                "name": "analysis_request",
                "description": "Request for analysis from analyst engine",
                "event_category": "analysis",
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "analysis_type": {"type": "string"},
                        "data_to_analyze": {"type": "object"},
                        "analysis_parameters": {"type": "object"}
                    },
                    "required": ["analysis_type", "data_to_analyze"]
                }
            },
            {
                "name": "tool_execution",
                "description": "Tool execution by an agent",
                "event_category": "interaction",
                "data_schema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string"},
                        "parameters": {"type": "object"},
                        "result": {"type": "object"}
                    },
                    "required": ["tool_name"]
                }
            }
        ]
        
        for event_data in basic_event_types:
            event_type = EventType(**event_data)
            db.add(event_type)
        
        db.commit()
        logger.info(f"Seeded {len(basic_event_types)} basic event types")
        
    except Exception as e:
        logger.error(f"Failed to seed initial data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """
    Reset the database by dropping and recreating all tables
    
    WARNING: This will delete all data!
    """
    from .models import Base
    
    logger.warning("Resetting database - ALL DATA WILL BE LOST!")
    
    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        
        # Recreate tables
        init_database()
        logger.info("Database reset completed successfully!")
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        raise


def get_database_info():
    """
    Get information about the current database state
    
    Returns:
        dict: Database information including table counts
    """
    from .models import (
        AgentTemplate, ScenarioTemplate, AgentInstance, ScenarioRun,
        EventType, EventInstance, ExecutionLog, EngineState
    )
    
    db = get_db_session()
    try:
        info = {
            "database_path": str(DB_PATH),
            "database_exists": DB_PATH.exists(),
            "table_counts": {
                "agent_templates": db.query(AgentTemplate).count(),
                "scenario_templates": db.query(ScenarioTemplate).count(),
                "agent_instances": db.query(AgentInstance).count(),
                "scenario_runs": db.query(ScenarioRun).count(),
                "event_types": db.query(EventType).count(),
                "event_instances": db.query(EventInstance).count(),
                "execution_logs": db.query(ExecutionLog).count(),
                "engine_states": db.query(EngineState).count()
            }
        }
        return info
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {"error": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    
    # Print database info
    info = get_database_info()
    print("\nDatabase Information:")
    print(f"Path: {info['database_path']}")
    print(f"Exists: {info['database_exists']}")
    print("\nTable Counts:")
    for table, count in info.get('table_counts', {}).items():
        print(f"  {table}: {count}")
