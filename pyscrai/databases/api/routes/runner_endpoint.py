from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
from pyscrai.engines.scenario_runner import ScenarioRunner
from pyscrai.databases.database import get_db_session

# Global ScenarioRunner instance (singleton for FastAPI app)
runner = None
def get_runner():
    global runner
    if runner is None:
        # Use a new DB session for the runner
        # The ScenarioRunner will hold and use this session.
        # Commits are handled within ScenarioRunner.
        # The session is not explicitly closed here, relies on app shutdown / GC for now,
        # which is an improvement over misusing __enter__ without __exit__.
        runner = ScenarioRunner(get_db_session())
    return runner

router = APIRouter(prefix="/api/v1/runner", tags=["runner"])

class StartScenarioRequest(BaseModel):
    template_name: str
    scenario_config: Optional[Dict[str, Any]] = None
    agent_configs: Optional[Dict[str, Any]] = None

@router.post("/scenario_execute_from_template")
async def execute_from_template(req: StartScenarioRequest):
    """Start a scenario from a template using the live ScenarioRunner."""
    runner = get_runner()
    try:
        scenario_id = await runner.start_scenario(
            template_name=req.template_name,
            scenario_config=req.scenario_config,
            agent_configs=req.agent_configs
        )
        return {"scenario_run_id": scenario_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start scenario: {e}")

class EventRequest(BaseModel):
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    target_agent_id: Optional[int] = None

@router.post("/{scenario_id}/dispatch_live_event")
async def dispatch_live_event(scenario_id: int, req: EventRequest):
    """Send a live event to a running scenario via the live ScenarioRunner."""
    runner = get_runner()
    try:
        result = await runner.send_event_to_scenario(
            scenario_run_id=scenario_id,
            event_type=req.event_type,
            event_data=req.event_data or {},
            target_agent_id=req.target_agent_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send event: {e}")

@router.get("/active_scenarios")
async def get_active_scenarios():
    """Return a list of currently active scenario IDs and their details."""
    runner_instance = get_runner()
    active_scenarios_details = []
    for scenario_id, scenario_data in runner_instance.active_scenarios.items():
        scenario_run = scenario_data.get("scenario_run")
        if scenario_run:
            active_scenarios_details.append(
                {
                    "id": scenario_run.id,
                    "name": scenario_run.name,
                    "status": scenario_run.status,
                    "started_at": scenario_run.started_at.isoformat() if scenario_run.started_at else None,
                    "template_id": scenario_run.template_id
                }
            )
        else:
            # Fallback if scenario_run object is not found (should ideally not happen)
            active_scenarios_details.append({"id": scenario_id, "name": "Unknown", "status": "Unknown"})
    return active_scenarios_details
