"""
Database initialization and configuration
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import os
from .models import Base

# Get database path
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)
db_path = data_dir / "pyscrai.db"

# Create engine
DATABASE_URL = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URL, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_database():
    """Initialize the database with all tables"""
    print(f"Initializing database at: {db_path}")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a database session (for direct usage)"""
    return SessionLocal()


if __name__ == "__main__":
    init_database()
