"""
API routes for template management (Agent and Scenario templates)
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database import get_db
from ...models.schemas import (
    AgentTemplateCreate,
    AgentTemplateUpdate,
    AgentTemplateResponse,
    ScenarioTemplateCreate,
    ScenarioTemplateUpdate,
    ScenarioTemplateResponse
)
from ....factories.template_manager import TemplateManager

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])

# Agent Template Endpoints
@router.post("/agents", response_model=AgentTemplateResponse)
async def create_agent_template(
    template_data: AgentTemplateCreate,
    db: Session = Depends(get_db)
) -> AgentTemplateResponse:
    """Create a new agent template"""
    try:
        manager = TemplateManager(db)
        template = manager.create_agent_template(template_data)
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/agents", response_model=List[AgentTemplateResponse])
async def list_agent_templates(
    db: Session = Depends(get_db)
) -> List[AgentTemplateResponse]:
    """List all agent templates"""
    try:
        manager = TemplateManager(db)
        templates = manager.list_agent_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/agents/{template_id}", response_model=AgentTemplateResponse)
async def get_agent_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> AgentTemplateResponse:
    """Get a specific agent template by ID"""
    try:
        manager = TemplateManager(db)
        template = manager.get_agent_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Agent template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/agents/by-name/{name}", response_model=AgentTemplateResponse)
async def get_agent_template_by_name(
    name: str,
    db: Session = Depends(get_db)
) -> AgentTemplateResponse:
    """Get a specific agent template by name"""
    try:
        manager = TemplateManager(db)
        template = manager.get_agent_template_by_name(name)
        if not template:
            raise HTTPException(status_code=404, detail="Agent template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/agents/{template_id}", response_model=AgentTemplateResponse)
async def update_agent_template(
    template_id: int,
    update_data: AgentTemplateUpdate,
    db: Session = Depends(get_db)
) -> AgentTemplateResponse:
    """Update an agent template"""
    try:
        manager = TemplateManager(db)
        template = manager.update_agent_template(template_id, update_data)
        if not template:
            raise HTTPException(status_code=404, detail="Agent template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/agents/{template_id}")
async def delete_agent_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Delete an agent template"""
    try:
        manager = TemplateManager(db)
        success = manager.delete_agent_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Agent template not found")
        return {"status": "success", "message": "Agent template deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Scenario Template Endpoints
@router.post("/scenarios", response_model=ScenarioTemplateResponse)
async def create_scenario_template(
    template_data: ScenarioTemplateCreate,
    db: Session = Depends(get_db)
) -> ScenarioTemplateResponse:
    """Create a new scenario template"""
    try:
        manager = TemplateManager(db)
        template = manager.create_scenario_template(template_data)
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scenarios", response_model=List[ScenarioTemplateResponse])
async def list_scenario_templates(
    db: Session = Depends(get_db)
) -> List[ScenarioTemplateResponse]:
    """List all scenario templates"""
    try:
        manager = TemplateManager(db)
        templates = manager.list_scenario_templates()
        return templates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scenarios/{template_id}", response_model=ScenarioTemplateResponse)
async def get_scenario_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> ScenarioTemplateResponse:
    """Get a specific scenario template by ID"""
    try:
        manager = TemplateManager(db)
        template = manager.get_scenario_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Scenario template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/scenarios/by-name/{name}", response_model=ScenarioTemplateResponse)
async def get_scenario_template_by_name(
    name: str,
    db: Session = Depends(get_db)
) -> ScenarioTemplateResponse:
    """Get a specific scenario template by name"""
    try:
        manager = TemplateManager(db)
        template = manager.get_scenario_template_by_name(name)
        if not template:
            raise HTTPException(status_code=404, detail="Scenario template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.put("/scenarios/{template_id}", response_model=ScenarioTemplateResponse)
async def update_scenario_template(
    template_id: int,
    update_data: ScenarioTemplateUpdate,
    db: Session = Depends(get_db)
) -> ScenarioTemplateResponse:
    """Update a scenario template"""
    try:
        manager = TemplateManager(db)
        template = manager.update_scenario_template(template_id, update_data)
        if not template:
            raise HTTPException(status_code=404, detail="Scenario template not found")
        return template
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/scenarios/{template_id}")
async def delete_scenario_template(
    template_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Delete a scenario template"""
    try:
        manager = TemplateManager(db)
        success = manager.delete_scenario_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Scenario template not found")
        return {"status": "success", "message": "Scenario template deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
