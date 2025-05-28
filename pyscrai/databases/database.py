"""
Database configuration and session management for PyScrAI.
Manages SQLite database connection, SQLAlchemy ORM setup,
table creation, and initial data seeding.
"""
import json
import logging
import sqlite3
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Database Configuration ---
try:
    # Assumes this file is in pyscrai/databases/
    # PROJECT_ROOT will be the 'pyscrai' parent directory
    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
except Exception as e:
    logger.error(f"Error determining PROJECT_ROOT: {e}. Assuming current directory's parent as fallback.")
    PROJECT_ROOT = Path(".").resolve().parent 

DATA_DIR = PROJECT_ROOT / "data"
DB_NAME = "pyscrai.db"
DB_PATH = DATA_DIR / DB_NAME

DATABASE_URL = f"sqlite:///{DB_PATH}"

# --- SQLAlchemy Engine Setup ---
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for detailed SQL logging
    pool_pre_ping=True,  # Check connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    connect_args={
        "check_same_thread": False,  # Required for SQLite with multi-threading (e.g., FastAPI)
        "timeout": 15  # Connection timeout in seconds
    }
)

# --- SQLite Specific PRAGMA Settings ---
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Sets SQLite PRAGMA for new connections.
    Enables foreign keys, WAL mode for better concurrency,
    and other performance optimizations.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA foreign_keys=ON;")
            cursor.execute("PRAGMA journal_mode=WAL;")      # Write-Ahead Logging
            cursor.execute("PRAGMA synchronous=NORMAL;")   # Less aggressive than FULL, safer than OFF
            cursor.execute("PRAGMA cache_size=-20000;")     # Advise SQLite to use up to 20MB for cache
            cursor.execute("PRAGMA temp_store=MEMORY;")   # Use memory for temporary tables
            logger.debug("SQLite PRAGMA settings applied.")
        except sqlite3.Error as e:
            logger.error(f"Error setting SQLite PRAGMA: {e}")
        finally:
            cursor.close()

# --- SQLAlchemy Session Setup ---
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # Keep objects accessible after commit (useful for background tasks)
)

# --- Database Utility Functions ---
def get_db() -> Generator[Session, None, None]:
    """
    Dependency for getting a database session, typically for web framework routes.
    Ensures the session is closed after use.
    Yields:
        Session: SQLAlchemy database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback() # Rollback in case of error
        raise
    finally:
        db.close()

def get_db_session() -> Session:
    """
    Provides a database session for direct usage (e.g., in scripts or non-request contexts).
    The caller is responsible for closing the session.
    Returns:
        Session: SQLAlchemy database session.
    """
    return SessionLocal()

def init_database():
    """
    Initializes the database:
    1. Creates the data directory if it doesn't exist.
    2. Creates all tables defined in the models.
    3. Seeds initial essential data.
    """
    from .models import Base # Local import to avoid circular dependencies
    from .models.execution_models import EventType # CORRECTED IMPORT FOR EventType

    try:
        logger.info(f"Ensuring data directory exists at: {DATA_DIR}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing PyScrAI database at: {DB_PATH}")

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully (or already exist).")

        # Seed initial data
        _seed_initial_data(EventType) # Pass the EventType model

        logger.info("Database initialization process completed.")

    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        raise

def _seed_initial_data(EventTypeModel):
    """
    Seeds the database with initial data, like default EventTypes and templates.
    
    This function:
    1. Seeds event types if the table is empty
    2. Imports agent templates from pyscrai/templates/agents
    3. Imports scenario templates from pyscrai/templates/scenarios
    4. Imports event type definitions from pyscrai/templates/events

    Args:
        EventTypeModel: The SQLAlchemy model class for EventType.
    """
    db = get_db_session()
    try:
        # --- Step 1: Seed Event Types ---
        # Check if EventTypes already exist
        if db.query(EventTypeModel).count() == 0:
            logger.info("Seeding initial EventType data...")
            # Default event types (fallback)
            basic_event_types_data = [
                {
                    "name": "agent_message", "description": "Message sent by an agent",
                    "event_category": "interaction",
                    "data_schema": {"type": "object", "properties": {"content": {"type": "string"}}}
                },
                {
                    "name": "system_notification", "description": "System-level notification",
                    "event_category": "system",
                    "data_schema": {"type": "object", "properties": {"message": {"type": "string"}}}
                },
                {
                    "name": "narrative_event", "description": "Narrative progression event",
                    "event_category": "narrative",
                    "data_schema": {"type": "object", "properties": {"description": {"type": "string"}}}
                },
            ]
              # Try to load event types from template/events directory
            events_dir = PROJECT_ROOT / "pyscrai" / "templates" / "events"
            if events_dir.exists() and events_dir.is_dir():
                event_json_files = list(events_dir.glob("*.json"))
                if event_json_files:
                    logger.info(f"Found {len(event_json_files)} event type definition files in {events_dir}")
                    basic_event_types_data = []  # Clear default if we have files
                    
                    for event_file in event_json_files:
                        try:
                            with open(event_file, 'r') as f:
                                event_data = json.load(f)
                                # Handle both single event and array of events
                                events_to_process = event_data if isinstance(event_data, list) else [event_data]
                                
                                for evt in events_to_process:
                                    # Map fields to match the expected schema
                                    # Convert 'schema' to 'data_schema'
                                    if "schema" in evt and "data_schema" not in evt:
                                        evt["data_schema"] = evt.pop("schema")
                                    
                                    # Convert 'category' to 'event_category'
                                    if "category" in evt and "event_category" not in evt:
                                        evt["event_category"] = evt.pop("category")
                                    
                                    # Remove fields that don't exist in the EventType model
                                    if "is_core" in evt:
                                        evt.pop("is_core")
                                        
                                basic_event_types_data.extend(events_to_process)
                        except Exception as e:
                            logger.error(f"Error loading event types from {event_file}: {e}")

            # Create event type records
            for event_data in basic_event_types_data:
                # Ensure data_schema is a dict if it's a string
                if isinstance(event_data.get("data_schema"), str):
                    try:
                        event_data["data_schema"] = json.loads(event_data["data_schema"])
                    except json.JSONDecodeError:
                        logger.error(f"Error decoding data_schema for event {event_data.get('name')}")
                        event_data["data_schema"] = {}  # Default to empty schema on error
                
                event_type = EventTypeModel(**event_data)
                db.add(event_type)
            
            db.commit()
            logger.info(f"Seeded {len(basic_event_types_data)} event types.")
        else:
            logger.info("Event types already exist, skipping seeding.")
        
        # --- Step 2: Import templates from pyscrai/templates directory ---
        # Import necessary modules for templates
        from ..factories.template_manager import TemplateManager
        from ..databases.models import AgentTemplate, ScenarioTemplate
        from ..databases.models.schemas import AgentTemplateCreate, ScenarioTemplateCreate
        
        # Initialize template manager with our session
        template_manager = TemplateManager(db)
        
        # Set paths to template directories
        templates_root = PROJECT_ROOT / "pyscrai" / "templates"
        agent_templates_dir = templates_root / "agents"
        scenario_templates_dir = templates_root / "scenarios"
        
        # --- Step 3: Import Agent Templates ---
        if agent_templates_dir.exists() and agent_templates_dir.is_dir():
            agent_json_files = list(agent_templates_dir.glob("*.json"))
            if agent_json_files:
                logger.info(f"Found {len(agent_json_files)} agent template files")
                imported_count = 0
                
                for agent_file in agent_json_files:
                    try:
                        # Check if template with this name already exists
                        with open(agent_file, 'r') as f:
                            data = json.load(f)
                        
                        if "name" not in data:
                            logger.warning(f"Agent template in {agent_file} has no name field, skipping")
                            continue
                        existing = template_manager.get_agent_template_by_name(data["name"])
                        if existing:
                            logger.info(f"Agent template '{data['name']}' already exists, skipping import")
                            continue
                        
                        # Import template
                        template = template_manager.import_agent_template_from_file(agent_file)
                        logger.info(f"Imported agent template: {template.name} (ID: {template.id}, Type: {template.engine_type})")
                        imported_count += 1
                    except ValueError as e:
                        logger.error(f"Validation error importing agent template {agent_file.name}: {e}")
                    except IOError as e:
                        logger.error(f"File read error importing agent template {agent_file.name}: {e}")
                    except Exception as e:
                        logger.error(f"Failed to import agent template {agent_file.name}: {str(e)}")
                
                logger.info(f"Imported {imported_count} new agent templates")
        
        # --- Step 4: Import Scenario Templates ---
        if scenario_templates_dir.exists() and scenario_templates_dir.is_dir():
            scenario_json_files = list(scenario_templates_dir.glob("*.json"))
            if scenario_json_files:
                logger.info(f"Found {len(scenario_json_files)} scenario template files")
                imported_count = 0
                
                for scenario_file in scenario_json_files:
                    try:
                        # Check if template with this name already exists
                        with open(scenario_file, 'r') as f:
                            data = json.load(f)
                        
                        if "name" not in data:
                            logger.warning(f"Scenario template in {scenario_file} has no name field, skipping")
                            continue
                            
                        existing = template_manager.get_scenario_template_by_name(data["name"])
                        if existing:
                            logger.info(f"Scenario template '{data['name']}' already exists, skipping import")
                            continue
                        
                        # Import template
                        template = template_manager.import_scenario_template_from_file(scenario_file)
                        logger.info(f"Imported scenario template: {template.name}")
                        imported_count += 1
                    except Exception as e:
                        logger.error(f"Failed to import scenario template {scenario_file}: {e}")
                
                logger.info(f"Imported {imported_count} new scenario templates")

    except Exception as e:
        logger.error(f"Failed to seed database: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

def reset_database(skip_confirmation: bool = False):
    """
    Resets the database by dropping and recreating all tables.
    WARNING: This will delete all existing data in the database!
    
    Args:
        skip_confirmation (bool): If True, skip the confirmation prompt
                                  Only use this in non-interactive scripts or with explicit warning
    """
    from .models import Base # Local import

    logger.warning(f"Resetting database at {DB_PATH} - ALL DATA WILL BE LOST!")
    
    # Get confirmation unless skipping
    if not skip_confirmation:
        confirmation = input("Are you sure you want to reset the database? Type 'yes' to confirm: ")
        if confirmation.lower() != 'yes':
            logger.info("Database reset cancelled by user.")
            return

    try:
        logger.info("Dropping all tables...")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully.")

        # Re-initialize the database (creates tables and seeds initial data)
        init_database()
        logger.info("Database reset and re-initialization completed successfully!")

    except Exception as e:
        logger.error(f"Database reset failed: {e}", exc_info=True)
        raise

def get_database_info() -> dict:
    """
    Retrieves information about the current database state, including table counts.
    Returns:
        dict: A dictionary containing database path, existence status, and table counts.
    """
    # Import models locally to avoid circular dependencies if this module is imported early
    from .models.core_models import AgentTemplate, ScenarioTemplate, AgentInstance, ScenarioRun
    from .models.execution_models import EventType, EventInstance, ExecutionLog, EngineState # CORRECTED IMPORT LOCATION FOR EventType
    
    db = get_db_session()
    info = {
        "database_path": str(DB_PATH),
        "database_exists": DB_PATH.exists(),
        "table_counts": {}
    }
    try:
        # Ensure all models you want to count are imported and listed here
        models_to_count = {
            "agent_templates": AgentTemplate,
            "scenario_templates": ScenarioTemplate,
            "agent_instances": AgentInstance,
            "scenario_runs": ScenarioRun,
            "event_types": EventType,
            "event_instances": EventInstance,
            "execution_logs": ExecutionLog,
            "engine_states": EngineState
        }
        for name, model_class in models_to_count.items():
            try:
                if model_class: # Check if the model class itself is not None
                    info["table_counts"][name] = db.query(model_class).count()
                else:
                    logger.warning(f"Model class for '{name}' is None. Skipping count.")
                    info["table_counts"][name] = "N/A (model not loaded)"
            except Exception as e:
                logger.warning(f"Could not count table {name} (using model {model_class.__name__ if model_class else 'None'}): {e}. Table might not exist or model not loaded correctly.")
                info["table_counts"][name] = "Error or N/A"
        
    except Exception as e:
        logger.error(f"Failed to get complete database info: {e}", exc_info=True)
        info["error"] = str(e)
    finally:
        db.close()
    return info

# --- Main execution block for direct script running ---
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PyScrAI Database Management")
    parser.add_argument('--init', action='store_true', help='Initialize database without prompting')
    parser.add_argument('--reset', action='store_true', help='Reset database without prompting (WARNING: deletes all data)')
    parser.add_argument('--info', action='store_true', help='Display database information')
    
    args = parser.parse_args()
    
    logger.info("Running database.py script directly...")
    
    # Process command line arguments
    if args.reset:
        logger.warning("Resetting database without confirmation (--reset flag used)")
        from .models import Base
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully.")
        init_database()
        logger.info("Database has been reset and re-initialized.")
    
    elif args.init:
        logger.info("Initializing database without prompting (--init flag used)")
        init_database()
    
    else:
        # Default behavior (no args or only --info)
        # Initialize database if it doesn't exist or is empty
        if not DB_PATH.exists():
            logger.info(f"{DB_NAME} not found. Initializing database.")
            init_database()
        else:
            logger.info(f"Database {DB_NAME} already exists at {DB_PATH}.")
            # Check if tables exist and have data
            db_info_check = get_database_info()
            event_types_count = db_info_check.get("table_counts", {}).get("event_types")
            core_tables_exist_and_populated = isinstance(event_types_count, int) and event_types_count > 0

            if not db_info_check.get("table_counts") or not core_tables_exist_and_populated:
                logger.info("Database exists but seems empty or core tables are missing/empty. Re-initializing.")
                init_database()

    # Print database info (always, or if --info flag is used)
    if not args.init and not args.reset or args.info:
        db_info = get_database_info()
        print("\n--- PyScrAI Database Information ---")
        print(f"  Path: {db_info.get('database_path')}")
        print(f"  Exists: {db_info.get('database_exists')}")
        if "error" in db_info:
            print(f"  Error retrieving info: {db_info['error']}")
        if db_info.get('table_counts'):
            print("\n  Table Counts:")
            for table, count in sorted(db_info['table_counts'].items()):
                print(f"    {table}: {count}")
        print("------------------------------------")
