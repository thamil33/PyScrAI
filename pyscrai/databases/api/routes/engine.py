"""
API routes for engine management and event processing - Updated for Universal Templates and Custom Engines
"""
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

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
from ...models.execution_models import EngineState, EventType, EventInstance, QueuedEvent

router = APIRouter(prefix="/api/v1/engines", tags=["engines"])

# Engine Management Endpoints
@router.post("/register", response_model=EngineStateResponse)
async def register_engine(
    registration: EngineRegistration,
    db: Session = Depends(get_db)
) -> EngineStateResponse:
    """Register a new engine instance"""
    try:
        # Generate unique engine ID
        engine_id = f"{registration.engine_type}_{registration.engine_id}_{uuid.uuid4().hex[:8]}"
        
        # Convert capabilities and resource limits to dict for JSON storage
        capabilities_dict = {
            "supported_event_types": registration.capabilities.supported_event_types,
            "max_concurrent_agents": registration.capabilities.max_concurrent_agents,
            "supports_streaming": registration.capabilities.supports_streaming,
            "supports_memory_persistence": registration.capabilities.supports_memory_persistence,
            "custom_capabilities": registration.capabilities.custom_capabilities
        }
        
        resource_limits_dict = {
            "max_concurrent_events": registration.resource_limits.max_concurrent_events,
            "memory_limit_mb": registration.resource_limits.memory_limit_mb,
            "cpu_limit_percent": registration.resource_limits.cpu_limit_percent,
            "max_processing_time_seconds": registration.resource_limits.max_processing_time_seconds
        }
        
        engine = EngineState(
            id=engine_id,
            engine_type=registration.engine_type.value,
            status="healthy",
            capabilities=capabilities_dict,
            resource_limits=resource_limits_dict,
            engine_metadata=registration.metadata,
            current_workload=0,
            active_agents=0,
            processed_events_count=0,
            error_count=0,
            last_heartbeat=datetime.utcnow()
        )
        
        db.add(engine)
        db.commit()
        db.refresh(engine)
        return engine
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to register engine: {str(e)}")


@router.put("/{engine_id}/heartbeat", response_model=EngineStateResponse)
async def update_heartbeat(
    engine_id: str,
    heartbeat: EngineHeartbeat,
    db: Session = Depends(get_db)
) -> EngineStateResponse:
    """Update engine heartbeat and status"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    try:
        # Update engine state
        engine.status = heartbeat.status
        engine.current_workload = heartbeat.current_workload
        engine.active_agents = heartbeat.active_agents
        engine.processed_events_count = heartbeat.processed_events_count
        engine.error_count = heartbeat.error_count
        engine.last_heartbeat = datetime.utcnow()
        
        # Update performance metrics
        if not engine.performance_metrics:
            engine.performance_metrics = {}
        engine.performance_metrics.update(heartbeat.resource_utilization)
        
        # Store last error if provided
        if heartbeat.last_error:
            engine.performance_metrics["last_error"] = heartbeat.last_error
            engine.performance_metrics["last_error_time"] = datetime.utcnow().isoformat()
        
        db.commit()
        db.refresh(engine)
        return engine
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update heartbeat: {str(e)}")


@router.delete("/{engine_id}")
async def deregister_engine(
    engine_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Deregister an engine instance"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    try:
        # Release any assigned events back to queue
        assigned_events = db.query(QueuedEvent).filter(
            QueuedEvent.assigned_engine_id == engine_id,
            QueuedEvent.status.in_(["assigned", "processing"])
        ).all()
        
        for queued_event in assigned_events:
            queued_event.status = "queued"
            queued_event.assigned_engine_id = None
            queued_event.assigned_at = None
        
        # Delete the engine
        db.delete(engine)
        db.commit()
        
        return {"status": "success", "message": "Engine instance deregistered successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to deregister engine: {str(e)}")


@router.get("/", response_model=List[EngineStateResponse])
async def list_engines(
    engine_type: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[EngineStateResponse]:
    """List all engine instances with optional filtering"""
    query = db.query(EngineState)
    
    if engine_type:
        query = query.filter(EngineState.engine_type == engine_type)
    if status:
        query = query.filter(EngineState.status == status)
    
    engines = query.order_by(EngineState.last_heartbeat.desc()).all()
    return engines


@router.get("/{engine_id}", response_model=EngineStateResponse)
async def get_engine(
    engine_id: str,
    db: Session = Depends(get_db)
) -> EngineStateResponse:
    """Get engine instance by ID"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    return engine


# Event Queue Management
@router.post("/queue/request", response_model=List[QueuedEventResponse])
async def request_events(
    request: EventQueueRequest,
    db: Session = Depends(get_db)
) -> List[QueuedEventResponse]:
    """Request events from queue for processing"""
    # Verify engine exists and is healthy
    engine = db.query(EngineState).filter(EngineState.id == request.engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    if engine.status not in ["healthy", "degraded"]:
        raise HTTPException(status_code=400, detail="Engine is not in a state to process events")
    
    try:
        # Get available events for this engine type
        query = db.query(QueuedEvent).filter(
            QueuedEvent.engine_type == request.engine_type.value,
            QueuedEvent.status == "queued"
        )
        
        # Apply filters if provided
        if request.priority_filter:
            query = query.filter(QueuedEvent.priority.in_(request.priority_filter))
        
        if request.event_type_filter:
            # Join with EventInstance and EventType to filter by event type names
            query = query.join(QueuedEvent.event_instance).join(EventInstance.event_type).filter(
                EventType.name.in_(request.event_type_filter)
            )
        
        # Get events ordered by priority and creation time
        events = query.order_by(
            QueuedEvent.priority.desc(),
            QueuedEvent.created_at.asc()
        ).limit(request.max_events).all()
        
        # Assign events to this engine
        for event in events:
            event.status = "assigned"
            event.assigned_engine_id = request.engine_id
            event.assigned_at = datetime.utcnow()
        
        db.commit()
        return events
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to request events: {str(e)}")


@router.put("/events/{event_id}/status")
async def update_event_status(
    event_id: int,
    status_update: EventStatusUpdate,
    db: Session = Depends(get_db)
) -> dict:
    """Update event processing status"""
    # Find the queued event
    queued_event = db.query(QueuedEvent).filter(
        QueuedEvent.event_instance_id == event_id
    ).first()
    
    if not queued_event:
        raise HTTPException(status_code=404, detail="Queued event not found")
    
    # Get the actual event instance
    event_instance = db.query(EventInstance).filter(EventInstance.id == event_id).first()
    if not event_instance:
        raise HTTPException(status_code=404, detail="Event instance not found")
    
    try:
        # Update event instance status
        event_instance.status = status_update.status
        
        if status_update.result:
            event_instance.processing_result = status_update.result
        
        if status_update.error:
            event_instance.error_info = {"error": status_update.error, "timestamp": datetime.utcnow().isoformat()}
        
        if status_update.processing_time_ms:
            if not event_instance.processing_result:
                event_instance.processing_result = {}
            event_instance.processing_result["processing_time_ms"] = status_update.processing_time_ms
        
        # Update queued event status
        if status_update.status == "completed":
            queued_event.status = "completed"
            queued_event.completed_at = datetime.utcnow()
            event_instance.processed_at = datetime.utcnow()
        elif status_update.status == "failed":
            queued_event.processing_attempts += 1
            if queued_event.processing_attempts >= queued_event.max_attempts:
                queued_event.status = "failed"
                event_instance.status = "failed"
            else:
                queued_event.status = "queued"  # Retry
                queued_event.assigned_engine_id = None
                queued_event.assigned_at = None
                event_instance.status = "pending"
        elif status_update.status == "processing":
            queued_event.status = "processing"
            event_instance.status = "processing"
        
        db.commit()
        return {"status": "success", "message": f"Event status updated to {status_update.status}"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update event status: {str(e)}")


# Health and Monitoring
@router.get("/health/system")
async def get_system_health(db: Session = Depends(get_db)) -> dict:
    """Get overall system health status"""
    try:
        # Engine statistics
        total_engines = db.query(EngineState).count()
        healthy_engines = db.query(EngineState).filter(EngineState.status == "healthy").count()
        degraded_engines = db.query(EngineState).filter(EngineState.status == "degraded").count()
        unhealthy_engines = db.query(EngineState).filter(EngineState.status == "unhealthy").count()
        
        # Find stale engines (no heartbeat in last 5 minutes)
        stale_threshold = datetime.utcnow() - timedelta(minutes=5)
        stale_engines = db.query(EngineState).filter(
            EngineState.last_heartbeat < stale_threshold
        ).count()
        
        # Event queue statistics
        queued_events = db.query(QueuedEvent).filter(QueuedEvent.status == "queued").count()
        processing_events = db.query(QueuedEvent).filter(QueuedEvent.status == "processing").count()
        failed_events = db.query(QueuedEvent).filter(QueuedEvent.status == "failed").count()
        
        # Determine overall system health
        if healthy_engines == 0:
            system_health = "critical"
        elif unhealthy_engines > healthy_engines:
            system_health = "degraded"
        elif stale_engines > 0 or degraded_engines > 0:
            system_health = "degraded"
        else:
            system_health = "healthy"
        
        return {
            "system_health": system_health,
            "timestamp": datetime.utcnow().isoformat(),
            "engines": {
                "total": total_engines,
                "healthy": healthy_engines,
                "degraded": degraded_engines,
                "unhealthy": unhealthy_engines,
                "stale": stale_engines
            },
            "events": {
                "queued": queued_events,
                "processing": processing_events,
                "failed": failed_events
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get system health: {str(e)}")


@router.get("/metrics/{engine_id}")
async def get_engine_metrics(
    engine_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """Get detailed metrics for a specific engine"""
    engine = db.query(EngineState).filter(EngineState.id == engine_id).first()
    if not engine:
        raise HTTPException(status_code=404, detail="Engine instance not found")
    
    # Get recent event processing stats
    recent_events = db.query(QueuedEvent).filter(
        QueuedEvent.assigned_engine_id == engine_id,
        QueuedEvent.assigned_at >= datetime.utcnow() - timedelta(hours=1)
    ).count()
    
    return {
        "engine_id": engine_id,
        "engine_type": engine.engine_type,
        "status": engine.status,
        "current_workload": engine.current_workload,
        "active_agents": engine.active_agents,
        "processed_events_count": engine.processed_events_count,
        "error_count": engine.error_count,
        "recent_events_processed": recent_events,
        "performance_metrics": engine.performance_metrics or {},
        "last_heartbeat": engine.last_heartbeat.isoformat() if engine.last_heartbeat else None,
        "uptime_hours": (datetime.utcnow() - engine.created_at).total_seconds() / 3600
    }
