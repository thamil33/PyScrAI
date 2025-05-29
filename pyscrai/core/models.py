"""
Core data models for PyScrAI.
"""
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class Event:
    '''
    Represents a generic event within the PyScrAI system.

    Attributes:
        event_type (str): The type of the event (e.g., 'actor_speech_generated', 
                          'scene_description_updated', 'request_analysis_update').
        payload (Dict[str, Any]): A dictionary containing the data specific to this event.
        source_entity_id (Optional[str]): The unique ID of the entity that generated this event.
        target_entity_id (Optional[str]): The unique ID of the entity this event is intended for.
                                         Can be None if the event is broadcast or for general consumption.
        event_id (uuid.UUID): A unique identifier for this specific event instance.
        timestamp (datetime): The UTC timestamp when the event was created.
    '''
    event_type: str
    payload: Dict[str, Any]
    source_entity_id: Optional[str] = None
    target_entity_id: Optional[str] = None
    event_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.utcnow())

    def __str__(self) -> str:
        return (f"Event(id={self.event_id}, type='{self.event_type}', "
                f"source='{self.source_entity_id}', target='{self.target_entity_id}', "
                f"ts='{self.timestamp.isoformat()}')")

# Example of how to create an event:
#
# from pyscrai.core.models import Event
#
# speech_event = Event(
#     event_type="actor_speech_generated",
#     payload={"actor_id": "primary_actor_123", "text": "Hello, world!", "confidence": 0.95},
#     source_entity_id="primary_actor_123"
# )
#
# analysis_request = Event(
#     event_type="request_analysis_update",
#     payload={"focus": "sentiment", "data_points": speech_event.payload},
#     source_entity_id="engine_manager_001",
#     target_entity_id="analyst_engine_456"
# )
#
# print(speech_event)
# print(analysis_request)

