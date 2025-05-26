"""Database connection configuration."""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Create data directory if it doesn't exist
project_root = Path(__file__).parent.parent.parent
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# Database URL
DATABASE_URL = f"sqlite:///{data_dir}/pyscrai.db"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # For SQLite
    echo=False  # Set to True for SQL debugging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
