"""
API routes for scenario management
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ...database import get_db
from ....databases.models.schemas import ScenarioRunCreate, ScenarioRunResponse
from ...models.schemas import (
    EventInstanceCreate,
    EventInstanceResponse
)
from ...models.scenario_models import ScenarioRun, ScenarioTemplate
from ...models.event_models import EventInstance, EventType
from ....factories.scenario_factory import ScenarioFactory

router = APIRouter(prefix="/api/v1/scenarios", tags=["scenarios"])

# Scenario Management Endpoints
@router.post("/", response_model=ScenarioRunResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    scenario_data: ScenarioRunCreate,
    db: Session = Depends(get_db)
) -> ScenarioRunResponse:
    """Create a new scenario instance from a template"""
    try:
        # Check if template exists
        template = db.query(ScenarioTemplate).filter(
            ScenarioTemplate.id == scenario_data.template_id
        ).first()
        
        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario template with ID {scenario_data.template_id} not found"
            )
        
        # Create scenario using ScenarioFactory
        factory = ScenarioFactory(db)
        scenario = factory.create_scenario_from_template(
            template_id=scenario_data.template_id,
            name=scenario_data.name,
            config=scenario_data.config
        )
        
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error creating scenario: {str(e)}"
        )

@router.get("/", response_model=List[ScenarioRunResponse])
async def get_scenarios(
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[ScenarioRunResponse]:
    """Get a list of scenario runs with optional filtering"""
    query = db.query(ScenarioRun)
    
    if status:
        query = query.filter(ScenarioRun.status == status)
    
    scenarios = query.order_by(ScenarioRun.created_at.desc()).limit(limit).offset(offset).all()
    return scenarios

@router.get("/{scenario_id}", response_model=ScenarioRunResponse)
async def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
) -> ScenarioRunResponse:
    """Get a specific scenario run by ID"""
    scenario = db.query(ScenarioRun).filter(ScenarioRun.id == scenario_id).first()
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario run with ID {scenario_id} not found"
        )
    return scenario

@router.post("/{scenario_id}/start", response_model=ScenarioRunResponse)
async def start_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
) -> ScenarioRunResponse:
    """Start execution of a scenario"""
    scenario = db.query(ScenarioRun).filter(ScenarioRun.id == scenario_id).first()
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario run with ID {scenario_id} not found"
        )
    
    if scenario.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start scenario in '{scenario.status}' status. Only pending scenarios can be started."
        )
    
    try:
        # Update scenario status to running
        scenario.status = "running"
        scenario.started_at = datetime.utcnow()
        db.commit()
        db.refresh(scenario)
        
        # Here we would trigger the actual scenario execution
        # This might involve creating initial events for the engines to process
        # For now, we'll just mark it as running
        
        return scenario
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error starting scenario: {str(e)}"
        )

@router.post("/{scenario_id}/stop", response_model=ScenarioRunResponse)
async def stop_scenario(
    scenario_id: int,
    db: Session = Depends(get_db)
) -> ScenarioRunResponse:
    """Stop execution of a running scenario"""
    scenario = db.query(ScenarioRun).filter(ScenarioRun.id == scenario_id).first()
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario run with ID {scenario_id} not found"
        )
    
    if scenario.status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop scenario in '{scenario.status}' status. Only running scenarios can be stopped."
        )
    
    try:
        # Update scenario status to stopped
        scenario.status = "stopped"
        db.commit()
        db.refresh(scenario)
        
        # Here we would handle cleanup of any running processes
        
        return scenario
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error stopping scenario: {str(e)}"
        )

@router.get("/{scenario_id}/events", response_model=List[EventInstanceResponse])
async def get_scenario_events(
    scenario_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
) -> List[EventInstanceResponse]:
    """Get events associated with a specific scenario"""
    # First check if scenario exists
    scenario = db.query(ScenarioRun).filter(ScenarioRun.id == scenario_id).first()
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario run with ID {scenario_id} not found"
        )
    
    events = db.query(EventInstance).filter(
        EventInstance.scenario_run_id == scenario_id
    ).order_by(EventInstance.timestamp.desc()).limit(limit).offset(offset).all()
    
    return events

@router.post("/{scenario_id}/events", response_model=EventInstanceResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario_event(
    scenario_id: int,
    event_data: EventInstanceCreate,
    db: Session = Depends(get_db)
) -> EventInstanceResponse:
    """Create a new event for a scenario"""
    # First check if scenario exists
    scenario = db.query(ScenarioRun).filter(ScenarioRun.id == scenario_id).first()
    if not scenario:
        raise HTTPException(
            status_code=404,
            detail=f"Scenario run with ID {scenario_id} not found"
        )
    
    # Check if event type exists
    event_type = db.query(EventType).filter(
        EventType.id == event_data.event_type_id
    ).first()
    if not event_type:
        raise HTTPException(
            status_code=404,
            detail=f"Event type with ID {event_data.event_type_id} not found"
        )
    
    # Create the event
    try:
        event = EventInstance(
            event_type_id=event_data.event_type_id,
            scenario_run_id=scenario_id,
            agent_instance_id=event_data.agent_instance_id,
            data=event_data.data,
            timestamp=datetime.utcnow()
        )
        
        db.add(event)
        db.commit()
        db.refresh(event)
        
        return event
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating event: {str(e)}"
        )
