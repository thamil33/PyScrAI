"""
Test script to create sample events for testing the event processing pipeline
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from pyscrai.databases.database import get_db
from pyscrai.databases.models.event_models import EventType, EventInstance

def create_test_events():
    """Create some test events for validation"""
    db = next(get_db())
    
    # Create test event types
    actor_event_type = EventType(
        name="dialogue_request",
        description="Request for an actor to generate dialogue",
        category="actor",
        engine_type="actor",
        schema={
            "type": "object",
            "properties": {
                "character_id": {"type": "string"},
                "context": {"type": "string"},
                "prompt": {"type": "string"}
            },
            "required": ["character_id", "prompt"]
        }
    )
    
    narrator_event_type = EventType(
        name="scene_description",
        description="Request for narrator to describe a scene",
        category="narrator", 
        engine_type="narrator",
        schema={
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "situation": {"type": "string"},
                "atmosphere": {"type": "string"}
            },
            "required": ["location", "situation"]
        }
    )
    
    db.add(actor_event_type)
    db.add(narrator_event_type)
    db.commit()
    db.refresh(actor_event_type)
    db.refresh(narrator_event_type)
    
    # Create test event instances
    test_events = [
        EventInstance(
            event_type_id=actor_event_type.id,
            data={
                "character_id": "pope_leo_xiii",
                "context": "Vatican study room, late evening",
                "prompt": "The Pope reflects on the supernatural vision he witnessed"
            },
            priority=5,
            status="queued"
        ),
        EventInstance(
            event_type_id=narrator_event_type.id,
            data={
                "location": "Vatican Gardens",
                "situation": "Strange lights appear in the sky",
                "atmosphere": "mysterious and otherworldly"
            },
            priority=3,
            status="queued"
        ),
        EventInstance(
            event_type_id=actor_event_type.id,
            data={
                "character_id": "cardinal_rampolla",
                "context": "Meeting with the Pope",
                "prompt": "Cardinal responds to the Pope's account of the vision"
            },
            priority=4,
            status="queued"
        )
    ]
    
    for event in test_events:
        db.add(event)
    
    db.commit()
    
    print(f"Created {len(test_events)} test events")
    print(f"Actor event type ID: {actor_event_type.id}")
    print(f"Narrator event type ID: {narrator_event_type.id}")
    
    db.close()

if __name__ == "__main__":
    create_test_events()
