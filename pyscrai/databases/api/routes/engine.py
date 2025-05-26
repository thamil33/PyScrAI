"""
API routes for engine management and event processing
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

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
    
    # Release any locked events before deregistering
    locked_events = db.query(EventInstance).filter(
        EventInstance.locked_by == engine_id,
        EventInstance.status == "processing"
    ).all()
    
    for event in locked_events:
        event.status = "queued"
        event.locked_by = None
        event.lock_until = None
    
    db.delete(engine)
    db.commit()
    return {"status": "success", "message": "Engine instance deregistered"}

@router.get("/engine-instances", response_model=List[EngineStateResponse])
async def list_engine_instances(db: Session = Depends(get_db)) -> List[EngineStateResponse]:
    """List all engine instances"""
    engines = db.query(EngineState).all()
    return engines

@router.get("/engine-instances/{engine_id}", response_model=EngineStateResponse)
async def get_engine_instance(engine_id: str, db: Session = Depends(get_db)) -> EngineStateResponse:
    """Get engine instance by ID"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    return engine

# Event Management Endpoints
@router.get("/events/queue/{engine_type}", response_model=list[QueuedEventResponse])
async def get_events_queue(
    engine_type: str,
    engine_id: str,  # Required for locking mechanism
    max_events: int = 5,  # Default to 5 as per Engine Team Communication
    capabilities: Optional[List[str]] = None,
    db: Session = Depends(get_db)
) -> list[QueuedEventResponse]:
    """Get events from queue for processing with locking mechanism"""
    
    # Verify engine exists
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    # Release expired locks first
    expired_time = datetime.utcnow()
    expired_events = db.query(EventInstance).filter(
        EventInstance.lock_until < expired_time,
        EventInstance.status == "processing"
    ).all()
    
    for event in expired_events:
        event.status = "queued"
        event.locked_by = None
        event.lock_until = None
    
    # Get available events
    query = (
        db.query(EventInstance)
        .join(EventType)
        .filter(
            EventType.engine_type == engine_type,
            EventInstance.status.in_(["queued", "retry"]),
            or_(
                EventInstance.lock_until.is_(None),
                EventInstance.lock_until < datetime.utcnow()
            )
        )
    )
    
    # Filter by capabilities if provided
    if capabilities:
        # Check if engine has required capabilities
        engine_capabilities = engine.engine_metadata.get("static_config", {}).get("capabilities", [])
        for cap in capabilities:
            if cap not in engine_capabilities:
                return []  # Engine doesn't have required capabilities
    
    events = (
        query.order_by(EventInstance.priority.desc(), EventInstance.created_at.asc())
        .limit(max_events)
        .all()
    )
    
    # Lock the events for this engine (5 minute lock)
    lock_until = datetime.utcnow() + timedelta(minutes=5)
    for event in events:
        event.status = "processing"
        event.locked_by = engine_id
        event.lock_until = lock_until
        
        # Track which engines have processed this event
        if not event.processed_by_engines:
            event.processed_by_engines = []
        if engine_id not in event.processed_by_engines:
            event.processed_by_engines.append(engine_id)
    
    db.commit()
    return events


@router.put("/events/{event_id}/status", response_model=dict[str, str])
async def update_event_status(
    event_id: int,
    status_update: EventStatusUpdate,
    engine_id: str,  # Required to verify ownership
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """Update event processing status"""
    event = db.query(EventInstance).filter(EventInstance.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Verify the engine has the lock on this event
    if event.locked_by != engine_id:
        raise HTTPException(status_code=403, detail="Event not locked by this engine")
    
    if status_update.status == "failed":
        # Handle retry logic
        event.retry_count = (event.retry_count or 0) + 1
        event.last_error = status_update.error
        
        # Check if max retries reached
        max_retries = 3  # Could be configurable
        if event.retry_count >= max_retries:
            event.status = "failed"
            event.locked_by = None
            event.lock_until = None
        else:
            event.status = "retry"
            event.locked_by = None
            event.lock_until = None
            # Set next retry time (exponential backoff)
            retry_delay = min(60 * (2 ** event.retry_count), 3600)  # Max 1 hour
            event.next_retry_time = datetime.utcnow() + timedelta(seconds=retry_delay)
    
    elif status_update.status == "completed":
        event.status = "completed"
        event.locked_by = None
        event.lock_until = None
        if status_update.result:
            event.result = status_update.result
        event.retry_count = 0
    
    else:
        # Other status updates
        event.status = status_update.status
        if status_update.result:
            event.result = status_update.result
            
    db.commit()
    return {"status": "success", "message": f"Event status updated to {status_update.status}"}

# Health check endpoint
@router.get("/engine-instances/health")
async def check_engine_health(db: Session = Depends(get_db)) -> dict:
    """Check overall engine health"""
    total_engines = db.query(EngineState).count()
    active_engines = db.query(EngineState).filter(EngineState.status == "active").count()
    
    # Find engines with stale heartbeats (no heartbeat in last 5 minutes)
    stale_threshold = datetime.utcnow() - timedelta(minutes=5)
    stale_engines = db.query(EngineState).filter(
        EngineState.last_heartbeat < stale_threshold
    ).count()
    
    # Count queued events
    queued_events = db.query(EventInstance).filter(
        EventInstance.status.in_(["queued", "retry"])
    ).count()
    
    return {
        "total_engines": total_engines,
        "active_engines": active_engines,
        "stale_engines": stale_engines,
        "queued_events": queued_events,
        "timestamp": datetime.utcnow().isoformat()
    }
