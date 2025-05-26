"""
Core system data seeding module for PyScrAI.

This module handles the loading and validation of core system data (e.g., event types,
system-level lookup values) that are essential for the system's operation.
"""

from pathlib import Path
import json, os, logging
from typing import List, Any, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SystemEventType(BaseModel):
    """Model for system-level event type definitions"""
    name: str = Field(..., description="Unique identifier for the event type")
    description: str = Field(..., description="Description of when/how this event occurs")
    data_schema: Dict[str, Any] = Field(default_factory=dict, description="JSON schema for event data")
    category: str = Field(..., description="Category of the event (e.g., system, agent, scenario)")
    is_core: bool = Field(default=False, description="Whether this is a core system event type")

class CoreSystemData:
    """Manager for core system data seeding"""
    
    def __init__(self, seeds_dir: Optional[str] = None):
        """Initialize with optional custom seeds directory path"""
        if seeds_dir is None:
            seeds_dir = os.path.dirname(__file__)
        self.seeds_dir = Path(seeds_dir)
        
    def load_system_event_types(self) -> List[SystemEventType]:
        """Load and validate system event type definitions"""
        event_types_file = self.seeds_dir / "event_types.json"
        if not event_types_file.exists():
            logger.warning(f"No event_types.json found in {self.seeds_dir}")
            return self._get_default_event_types()
            
        try:
            raw = json.loads(event_types_file.read_text())
            
            # rename "schema" key to "data_schema"
            for evt in raw:
                if "schema" in evt:
                    evt["data_schema"] = evt.pop("schema")
            
            # Validate each event type definition
            event_types = [SystemEventType(**evt) for evt in raw]
            logger.info(f"Loaded {len(event_types)} system event types")
            return event_types
            
        except Exception as e:
            logger.error(f"Error loading system event types: {e}")
            return self._get_default_event_types()
    
    def _get_default_event_types(self) -> List[SystemEventType]:
        """Provide default core system event types"""
        return [
            SystemEventType(
                name="agent_message",
                description="Message sent from one agent to another",
                data_schema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string"},
                        "from_agent": {"type": "string"},
                        "to_agent": {"type": "string"},
                    },
                    "required": ["content", "from_agent", "to_agent"]
                },
                category="agent",
                is_core=True
            ),
            SystemEventType(
                name="scenario_update",
                description="Update to scenario state or progress",
                data_schema={
                    "type": "object",
                    "properties": {
                        "status": {"type": "string"},
                        "turn": {"type": "integer"},
                        "data": {"type": "object"}
                    },
                    "required": ["status"]
                },
                category="scenario",
                is_core=True
            ),
            SystemEventType(
                name="error_occurred",
                description="System or runtime error event",
                data_schema={
                    "type": "object",
                    "properties": {
                        "error_type": {"type": "string"},
                        "message": {"type": "string"},
                        "stack_trace": {"type": "string"}
                    },
                    "required": ["error_type", "message"]
                },
                category="system",
                is_core=True
            )
        ]
