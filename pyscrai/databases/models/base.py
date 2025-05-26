"""Base database model configuration."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Create a single MetaData instance to be shared across all models
metadata = MetaData()

class Base(DeclarativeBase):
    """Base class for all database models."""
    metadata = metadata
    metadata = metadata
