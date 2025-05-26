"""
API routes for engine management and event processing
"""
import uuid
from datetime import datetime
from typing import List

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.schemas import (
    EngineRegistration, 
    EngineHeartbeat, 
    EngineStateResponse,
    EventQueueRequest,
    EventStatusUpdate,
    QueuedEventResponse
)
from ...models.engine_models import EngineState
from ...models.event_models import EventType, EventInstance

# Dependency
DBSession = Annotated[Session, Depends(get_db)]

router = APIRouter(prefix="/api/v1")

# Engine Management Endpoints
@router.post("/engine-instances", response_model=EngineStateResponse)
async def register_engine(
    registration: EngineRegistration,
    db: Session = Depends(get_db)
) -> EngineStateResponse:
    """Register a new engine instance"""
    # Convert ResourceLimits to dict for JSON serialization
    resource_limits_dict = {
        "max_concurrent_events": registration.resource_limits.max_concurrent_events,
        "memory_limit_mb": registration.resource_limits.memory_limit_mb
    }
    
    engine = EngineState(
        id=str(uuid.uuid4()),
        engine_type=registration.engine_type,
        status="active",
        last_heartbeat=datetime.utcnow(),
        current_workload=0,
        engine_metadata={
            "static_config": {
                "capabilities": registration.capabilities,
                "resource_limits": resource_limits_dict
            },
            "dynamic_state": {
                "resource_utilization": {}
            }
        }
    )
    
    db.add(engine)
    db.commit()
    db.refresh(engine)
    return engine


@router.put("/engine-instances/{engine_id}/heartbeat", response_model=EngineStateResponse)
async def update_heartbeat(
    engine_id: str,
    heartbeat: EngineHeartbeat,
    db: Session = Depends(get_db)
) -> EngineStateResponse:
    """Update engine heartbeat and status"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    engine.status = heartbeat.status
    engine.current_workload = heartbeat.current_workload
    engine.last_heartbeat = datetime.utcnow()
    
    # Properly update nested JSON field to trigger change detection
    metadata = engine.engine_metadata or {}
    dynamic_state = metadata.get("dynamic_state", {})
    # Merge existing resource utilization with new data
    existing_util = dynamic_state.get("resource_utilization", {})
    existing_util.update(heartbeat.resource_utilization)
    dynamic_state["resource_utilization"] = existing_util
    metadata["dynamic_state"] = dynamic_state
    engine.engine_metadata = metadata
    
    db.commit()
    db.refresh(engine)
    return engine


@router.delete("/engine-instances/{engine_id}")
async def deregister_engine(
    engine_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Deregister an engine instance"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    db.delete(engine)
    db.commit()
    return {"status": "success", "message": "Engine instance deregistered"}

# Event Management Endpoints
@router.get("/events/queue/{engine_type}", response_model=list[QueuedEventResponse])
async def get_events_queue(
    engine_type: str,
    max_events: int = 10,
    capabilities: list[str] = [],
    db: Session = Depends(get_db)
) -> list[QueuedEventResponse]:
    """Get events from queue for processing"""
    # Get events that match the engine type and haven't been processed
    query = (
        db.query(EventInstance)
        .join(EventType)
        .filter(
            EventType.engine_type == engine_type,
            EventInstance.status.in_(["queued", "retry"]),
        )
    )
    # Filter events by capabilities if provided
    if capabilities:
        # Assuming event data has a 'required_capabilities' field listing needed capabilities
        query = query.filter(
            EventInstance.data["required_capabilities"].astext.cast("jsonb").contains(capabilities)
        )
    # Exclude events already processed by any engine
    query = query.filter(
        (EventInstance.processed_by_engines.is_(None) | (EventInstance.processed_by_engines == []))
    )
    events = (
        query.order_by(EventInstance.priority.desc(), EventInstance.created_at.asc())
        .limit(max_events)
        .all()
    )
    return events  # Return all available events, empty list if none


@router.put("/events/{event_id}/status", response_model=dict[str, str])
async def update_event_status(
    event_id: int,
    status_update: EventStatusUpdate,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Update event processing status"""
    event = db.query(EventInstance).filter(EventInstance.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    if status_update.status == "failed":
        # Handle retry logic
        if not event.processed_by_engines:
            event.processed_by_engines = []
        
        # Increment retry count
        event.retry_count = (event.retry_count or 0) + 1
        
        # Check if max retries reached (3 for now)
        if event.retry_count >= 3:
            event.status = "failed"
            event.last_error = status_update.error
            # Remove from queue by clearing processed_by_engines to prevent re-queuing
            event.processed_by_engines = []
        else:
            event.status = "retry"
            event.last_error = status_update.error
    else:
        event.status = status_update.status
        if status_update.result:
            event.result = status_update.result
        # Reset retry count on success or other non-failed status
        event.retry_count = 0
        # Clear processed_by_engines on success to allow re-queuing if needed
        event.processed_by_engines = []
            
    db.commit()
    db.refresh(event)
    return {"status": "success"}
