"""
API endpoints for engine management and event processing
"""
from datetime import datetime, timedelta
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from ..models.schemas import (
    EngineRegistration, 
    EngineHeartbeat, 
    EngineStateResponse,
    EventQueueRequest,
    EventStatusUpdate,
    QueuedEventResponse
)
from ..models.engine_models import EngineState
from ..models.event_models import EventInstance, EventType
from ..database import get_db

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
        metadata={
            "static_config": {
                "capabilities": registration.capabilities,
                "resource_limits": registration.resource_limits
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
    engine.metadata["dynamic_state"]["resource_utilization"] = heartbeat.resource_utilization
    
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
    request: EventQueueRequest,
    db: Session = Depends(get_db)
) -> List[QueuedEventResponse]:
    """Get next batch of events for processing"""
    # Find events that are:
    # 1. Queued or failed (with retry)
    # 2. Not locked or lock expired
    # 3. Match engine type
    now = datetime.utcnow()
    
    query = db.query(EventInstance).join(EventType).filter(
        and_(
            EventType.engine_type == engine_type,
            or_(
                EventInstance.status == "queued",
                and_(
                    EventInstance.status == "failed",
                    EventInstance.retry_count < 3,
                    EventInstance.next_retry_time <= now
                )
            ),
            or_(
                EventInstance.lock_until.is_(None),
                EventInstance.lock_until <= now
            )
        )
    ).order_by(
        EventInstance.priority.desc(),
        EventInstance.created_at.asc()
    ).limit(request.batch_size)
    
    events = query.all()
    
    # Lock the events
    lock_until = now + timedelta(minutes=5)
    for event in events:
        event.status = "processing"
        event.lock_until = lock_until
        event.locked_by = request.engine_id
    
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
        if not event.processed_by_engines:
            event.processed_by_engines = []
        event.processed_by_engines.append({
            "engine_id": event.locked_by,
            "completed_at": datetime.utcnow().isoformat(),
            "result": update.result
        })
    elif update.status == "failed":
        event.retry_count += 1
        event.last_error = update.error
        if event.retry_count < 3:
            # Exponential backoff for retries
            delay = 30 * (2 ** (event.retry_count - 1))  # 30s, 60s, 120s
            event.next_retry_time = datetime.utcnow() + timedelta(seconds=delay)
            event.status = "queued"
        else:
            event.status = "failed"
    
    event.lock_until = None
    event.locked_by = None
    
    db.commit()
    return {"status": "success", "message": f"Event status updated to {update.status}"}
