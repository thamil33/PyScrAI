"""
API endpoints for engine management and event processing
"""
from datetime import datetime, timedelta
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

# Update imports to use the correct model structure
from ..models.schemas import (
    EngineRegistration, 
    EngineHeartbeat, 
    EngineStateResponse,
    EventQueueRequest,
    EventStatusUpdate,
    QueuedEventResponse
)
from ..models.execution_models import EngineState
# Fix: Import from models package directly since EventInstance/EventType might be in different modules
from ..models import EventInstance, EventType
from .. import get_db

router = APIRouter(prefix="/api/v1", tags=["engines"])

# Engine Management Endpoints
@router.post("/engine-instances", response_model=EngineStateResponse)
async def register_engine(
    registration: EngineRegistration,
    db: Session = Depends(get_db)
) -> EngineStateResponse:
    """Register a new engine instance"""
    engine = EngineState(
        id=str(uuid.uuid4()),
        engine_type=registration.engine_type,
        status="active",
        last_heartbeat=datetime.utcnow(),
        current_workload=0,
        engine_metadata={
            "static_config": {
                "capabilities": registration.capabilities,
                "resource_limits": registration.resource_limits.model_dump()
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
    engine.engine_metadata["dynamic_state"]["resource_utilization"] = heartbeat.resource_utilization
    
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


# Event Processing Endpoints
@router.get("/events/queue/{engine_type}", response_model=List[QueuedEventResponse])
async def get_events_for_processing(
    engine_type: str,
    engine_id: str = Query(..., description="Engine ID requesting events"),
    batch_size: int = Query(10, description="Number of events to retrieve"),
    db: Session = Depends(get_db)
) -> List[QueuedEventResponse]:
    """Get next batch of events for processing"""
    # Find events that are:
    # 1. Pending or failed (with retry)
    # 2. Not assigned or assignment expired
    # 3. Match engine type priority
    now = datetime.utcnow()
    
    query = db.query(EventInstance).join(EventType).filter(
        and_(
            or_(
                EventInstance.status == "pending",
                and_(
                    EventInstance.status == "failed",
                    EventInstance.processing_attempts < 3
                )
            ),
            or_(
                EventInstance.assigned_engine_id.is_(None),
                EventInstance.assigned_at < now - timedelta(minutes=5)  # Assignment expired
            )
        )
    ).order_by(
        EventInstance.priority.desc(),
        EventInstance.timestamp.asc()
    ).limit(batch_size)
    
    events = query.all()
    
    # Assign the events to this engine
    for event in events:
        event.status = "processing"
        event.assigned_engine_id = engine_id
        event.assigned_at = now
        event.processing_attempts += 1
    
    db.commit()
    
    return events


@router.put("/events/{event_id}/status")
async def update_event_status(
    event_id: int,
    update: EventStatusUpdate,
    db: Session = Depends(get_db)
) -> dict:
    """Update event processing status"""
    event = db.query(EventInstance).filter(EventInstance.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event.status = update.status
    if update.status == "completed":
        event.processing_result = update.result or {}
        event.processed_at = datetime.utcnow()
    elif update.status == "failed":
        event.error_info = {"error": update.error} if update.error else {}
        if event.processing_attempts < 3:
            event.status = "pending"  # Will be retried
        else:
            event.status = "failed"  # Max attempts reached
    
    event.assigned_engine_id = None
    event.assigned_at = None
    
    db.commit()
    return {"status": "success", "message": f"Event status updated to {update.status}"}