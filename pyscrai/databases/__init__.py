"""
PyScrAI Database Package - Universal Templates and Custom Engines

This package provides database models, configuration, and utilities for the PyScrAI system
with support for universal generic templates and custom engines (Actor, Analyst, Narrator).
"""

# Ensure models are only imported once
from .models import (
    Base,
    # Core template models
    AgentTemplate,
    ScenarioTemplate,
    # Execution models
    AgentInstance,
    ScenarioRun,
    EventType,
    EventInstance,
    ExecutionLog,
    EngineState,
    QueuedEvent,
    SystemMetrics,
    TemplateUsage
)

from .database import (
    engine,
    SessionLocal,
    get_db,
    get_db_session,
    init_database,
    reset_database,
    get_database_info,
    DATABASE_URL,
    DB_PATH
)

# Version and metadata
__version__ = "2.0.0"
__description__ = "PyScrAI Database Layer - Universal Templates and Custom Engines"

# Export all public interfaces
__all__ = [
    # Database configuration and utilities
    "engine",
    "SessionLocal", 
    "get_db",
    "get_db_session",
    "init_database",
    "reset_database",
    "get_database_info",
    "DATABASE_URL",
    "DB_PATH",
    
    # Models
    "Base",
    "AgentTemplate",
    "ScenarioTemplate", 
    "AgentInstance",
    "ScenarioRun",
    "EventType",
    "EventInstance",
    "ExecutionLog",
    "EngineState",
    "QueuedEvent",
    "SystemMetrics",
    "TemplateUsage",
    
    # Metadata
    "__version__",
    "__description__"
]


def initialize_system():
    """
    Initialize the complete PyScrAI database system
    
    This function:
    1. Creates all database tables
    2. Seeds initial data
    3. Validates the system is ready
    
    Returns:
        bool: True if initialization successful
    """
    try:
        print("🚀 Initializing PyScrAI Database System...")
        print(f"📍 Database location: {DB_PATH}")
        
        # Initialize database
        init_database()
        
        # Get system info
        info = get_database_info()
        
        print("✅ Database initialization completed!")
        print(f"📊 System ready with {sum(info['table_counts'].values())} total records")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


def get_system_status():
    """
    Get comprehensive system status
    
    Returns:
        dict: System status information
    """
    try:
        info = get_database_info()
        
        status = {
            "database_ready": info.get("database_exists", False),
            "database_path": info.get("database_path"),
            "total_records": sum(info.get("table_counts", {}).values()),
            "table_counts": info.get("table_counts", {}),
            "system_health": "healthy" if info.get("database_exists") else "needs_initialization"
        }
        
        return status
        
    except Exception as e:
        return {
            "database_ready": False,
            "error": str(e),
            "system_health": "error"
        }


if __name__ == "__main__":
    # Initialize system when run directly
    success = initialize_system()
    
    if success:
        status = get_system_status()
        print("\n📋 System Status:")
        print(f"   Health: {status['system_health']}")
        print(f"   Total Records: {status['total_records']}")
        print(f"   Database Ready: {status['database_ready']}")
    else:
        print("\n❌ System initialization failed!")
