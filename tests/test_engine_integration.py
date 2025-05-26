# tests/test_engine_integration.py
"""
Integration tests for PyScrAI engines, focusing on their main loop,
event processing, and API interactions (using mocks).
"""
import asyncio
import json 
import logging
import os # Re-added for OPENROUTER_API_KEY check in examples
from datetime import datetime, timezone 
from typing import Any, Dict, AsyncGenerator 
from unittest.mock import AsyncMock 

import pytest
import pytest_asyncio 
from httpx import Response, Request 

from pytest_httpx import HTTPXMock # type: ignore

from pyscrai.engines.actor_engine import ActorEngine
from pyscrai.engines.analyst_engine import AnalystEngine 
from pyscrai.engines.narrator_engine import NarratorEngine
from pyscrai.engines.base_engine import PYSCRAI_API_BASE_URL 
from pyscrai.databases.models.schemas import (
    EngineStateResponse,
    QueuedEventResponse,
    # EngineRegistration, # Commented: Unused in current test
    # EventStatusUpdate, # Commented: Unused in current test
    # EngineHeartbeat, # Commented: Unused in current test
    # ResourceLimits, # Commented: Unused in current test
)
from agno.run.response import RunResponse 

# Configure basic logging for tests to see engine logs
logger = logging.getLogger(__name__) 
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# --- Helper Function for Dummy API Keys ---
def set_dummy_api_keys(monkeypatch):
    """Sets dummy API keys for testing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", os.getenv("OPENROUTER_API_KEY", "test_dummy_openrouter_key"))
    monkeypatch.setenv("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", "test_dummy_openai_key"))
    monkeypatch.setenv("LMSTUDIO_API_KEY", os.getenv("LMSTUDIO_API_KEY", "test_dummy_lmstudio_key"))

# --- ActorEngine Fixtures ---

@pytest_asyncio.fixture
async def actor_engine_config() -> Dict[str, Any]:
    """Provides a default configuration for the ActorEngine."""
    return {
        "agent_config": {
            "model_config": {"id": "mistralai/mistral-7b-instruct:free", "temperature": 0.7},
            "personality_config": {"name": "Test Actor Agent"},
        },
        "engine_name": "TestActorEngine",
        "character_name": "TestCharacter",
        "personality_traits": "Brave and curious.",
        "storage_path": ":memory:", 
        "model_provider": "openrouter", 
        "api_base_url": PYSCRAI_API_BASE_URL 
    }

@pytest_asyncio.fixture
async def initialized_actor_engine(
    actor_engine_config: Dict[str, Any], 
    httpx_mock: HTTPXMock,
    monkeypatch 
) -> AsyncGenerator[ActorEngine, None]:
    set_dummy_api_keys(monkeypatch)
    engine = ActorEngine(**actor_engine_config)
    mock_engine_id = engine.engine_id 
    registration_response_data = EngineStateResponse(
        id=mock_engine_id, engine_type=engine.engine_type, status="registered",
        last_heartbeat=datetime.now(timezone.utc), current_workload=0,
        engine_metadata={
            "name": engine.engine_name, "capabilities": [engine.engine_type, "general_processing"],
            "resource_limits": {"max_concurrent_events": 1, "memory_limit_mb": 512}
        }
    ).model_dump(by_alias=True)
    httpx_mock.add_response(method="POST", url=f"{PYSCRAI_API_BASE_URL}/engine-instances/", json=registration_response_data, status_code=201)
    httpx_mock.add_response(method="GET", url=f"{PYSCRAI_API_BASE_URL}/engine-instances/{mock_engine_id}/state", json=registration_response_data, status_code=200)
    
    await engine.initialize(register_with_server=True)
    assert engine.initialized and engine.agent is not None
    yield engine 
    await engine.close_api_client()
    logger.info(f"ActorEngine '{engine.engine_name}' torn down.")

# --- AnalystEngine Fixtures ---

@pytest_asyncio.fixture
async def analyst_engine_config() -> Dict[str, Any]:
    """Provides a default configuration for the AnalystEngine."""
    return {
        "agent_config": {
            "model_config": {"id": "mistralai/mistral-7b-instruct:free", "temperature": 0.5},
            "personality_config": {"name": "Test Analyst Agent"},
        },
        "engine_name": "TestAnalystEngine",
        "analytical_focus": "Identifying key patterns in text.",
        "storage_path": ":memory:",
        "model_provider": "openrouter",
        "api_base_url": PYSCRAI_API_BASE_URL
    }

@pytest_asyncio.fixture
async def initialized_analyst_engine(
    analyst_engine_config: Dict[str, Any],
    httpx_mock: HTTPXMock,
    monkeypatch
) -> AsyncGenerator[AnalystEngine, None]:
    set_dummy_api_keys(monkeypatch)
    engine = AnalystEngine(**analyst_engine_config)
    mock_engine_id = engine.engine_id
    registration_response_data = EngineStateResponse(
        id=mock_engine_id, engine_type=engine.engine_type, status="registered",
        last_heartbeat=datetime.now(timezone.utc), current_workload=0,
        engine_metadata={
            "name": engine.engine_name, "capabilities": [engine.engine_type, "data_analysis"],
            "resource_limits": {"max_concurrent_events": 1, "memory_limit_mb": 512}
        }
    ).model_dump(by_alias=True)
    httpx_mock.add_response(method="POST", url=f"{PYSCRAI_API_BASE_URL}/engine-instances/", json=registration_response_data, status_code=201)
    httpx_mock.add_response(method="GET", url=f"{PYSCRAI_API_BASE_URL}/engine-instances/{mock_engine_id}/state", json=registration_response_data, status_code=200)

    await engine.initialize(register_with_server=True)
    assert engine.initialized and engine.agent is not None
    yield engine
    await engine.close_api_client()
    logger.info(f"AnalystEngine '{engine.engine_name}' torn down.")

# --- NarratorEngine Fixtures ---

@pytest_asyncio.fixture
async def narrator_engine_config() -> Dict[str, Any]:
    """Provides a default configuration for the NarratorEngine."""
    return {
        "agent_config": {
            "model_config": {"id": "mistralai/mistral-7b-instruct:free", "temperature": 0.8},
            "personality_config": {"name": "Test Narrator Agent"},
        },
        "engine_name": "TestNarratorEngine",
        "narrative_style": "Descriptive and engaging.",
        "storage_path": ":memory:",
        "model_provider": "openrouter",
        "api_base_url": PYSCRAI_API_BASE_URL
    }

@pytest_asyncio.fixture
async def initialized_narrator_engine(
    narrator_engine_config: Dict[str, Any],
    httpx_mock: HTTPXMock,
    monkeypatch
) -> AsyncGenerator[NarratorEngine, None]:
    set_dummy_api_keys(monkeypatch)
    engine = NarratorEngine(**narrator_engine_config)
    mock_engine_id = engine.engine_id
    registration_response_data = EngineStateResponse(
        id=mock_engine_id, engine_type=engine.engine_type, status="registered",
        last_heartbeat=datetime.now(timezone.utc), current_workload=0,
        engine_metadata={
            "name": engine.engine_name, "capabilities": [engine.engine_type, "scene_description"],
            "resource_limits": {"max_concurrent_events": 1, "memory_limit_mb": 512}
        }
    ).model_dump(by_alias=True)
    httpx_mock.add_response(method="POST", url=f"{PYSCRAI_API_BASE_URL}/engine-instances/", json=registration_response_data, status_code=201)
    httpx_mock.add_response(method="GET", url=f"{PYSCRAI_API_BASE_URL}/engine-instances/{mock_engine_id}/state", json=registration_response_data, status_code=200)
    
    await engine.initialize(register_with_server=True)
    assert engine.initialized and engine.agent is not None
    yield engine
    await engine.close_api_client()
    logger.info(f"NarratorEngine '{engine.engine_name}' torn down.")

# --- Generic Test Logic ---

async def _test_engine_main_loop_processes_one_event(
    engine: Any, httpx_mock: HTTPXMock, event_prompt_key: str, sample_prompt: str, mock_response_content: str
):
    """
    Generic test logic for an engine's main_loop processing a single event.
    """
    mock_engine_id = engine.engine_id
    
    sample_event_id = hash(sample_prompt) % 10000 # Generate a somewhat unique ID
    sample_event_data = {event_prompt_key: sample_prompt}
    
    queued_event_response_data = QueuedEventResponse(
        id=sample_event_id, event_type_id=1, status="queued", priority=1,
        data=sample_event_data, processed_by_engines=[], created_at=datetime.now(timezone.utc) 
    ).model_dump(by_alias=True)

    httpx_mock.add_response(
        method="GET", url=f"{PYSCRAI_API_BASE_URL}/events/queue/{engine.engine_type}?limit=1", 
        json=[queued_event_response_data], status_code=200,
    )
    httpx_mock.add_response(
        method="GET", url=f"{PYSCRAI_API_BASE_URL}/events/queue/{engine.engine_type}?limit=1",
        json=[], status_code=200,
    )

    updated_event_status_payload = None
    def capture_event_status_update(request: Request) -> Response:
        nonlocal updated_event_status_payload
        updated_event_status_payload = json.loads(request.content) 
        logger.debug(f"Mock API captured event status update for event {sample_event_id}: {updated_event_status_payload}")
        return Response(200, json={"message": "Status updated"})

    httpx_mock.add_callback(
        capture_event_status_update, method="PUT",
        url=f"{PYSCRAI_API_BASE_URL}/events/{sample_event_id}/status"
    )
    
    heartbeat_count = 0
    def count_heartbeats(request: Request) -> Response:
        nonlocal heartbeat_count
        heartbeat_count += 1
        logger.debug(f"Mock API received heartbeat #{heartbeat_count} for {engine.engine_name}")
        return Response(200, json={"message": "Heartbeat received"})

    httpx_mock.add_callback(
        count_heartbeats, method="PUT",
        url=f"{PYSCRAI_API_BASE_URL}/engine-instances/{mock_engine_id}/heartbeat"
    )

    if engine.agent: 
        engine.agent.arun = AsyncMock(return_value=RunResponse(content=mock_response_content, messages=[])) 

    loop_task = asyncio.create_task(engine.main_loop(poll_interval=0.1)) 
    await asyncio.sleep(0.5) 
    loop_task.cancel()
    try:
        await loop_task
    except asyncio.CancelledError:
        logger.info(f"Engine '{engine.engine_name}' main_loop task cancelled for test.")

    if engine.agent and isinstance(engine.agent.arun, AsyncMock):
        engine.agent.arun.assert_called_once()
        
    assert updated_event_status_payload is not None, f"Event status update not captured for {engine.engine_name}"
    assert updated_event_status_payload["status"] == "completed"
    assert updated_event_status_payload["result"]["content"] == mock_response_content
    assert updated_event_status_payload["error"] is None
    
    assert heartbeat_count > 0, f"No heartbeats sent for {engine.engine_name}"
    logger.info(f"Test for {engine.engine_name} completed successfully.")


# --- Test Cases ---

@pytest.mark.asyncio
async def test_actor_engine_main_loop_processes_one_event(
    initialized_actor_engine: ActorEngine, httpx_mock: HTTPXMock
):
    await _test_engine_main_loop_processes_one_event(
        engine=initialized_actor_engine,
        httpx_mock=httpx_mock,
        event_prompt_key="prompt",
        sample_prompt="A mysterious stranger offers you a quest. What do you do?",
        mock_response_content="I accept the quest with valor!"
    )

@pytest.mark.asyncio
async def test_analyst_engine_main_loop_processes_one_event(
    initialized_analyst_engine: AnalystEngine, httpx_mock: HTTPXMock
):
    await _test_engine_main_loop_processes_one_event(
        engine=initialized_analyst_engine,
        httpx_mock=httpx_mock,
        event_prompt_key="data_to_analyze", # AnalystEngine expects 'data_to_analyze'
        sample_prompt="Log data: UserA logged in. UserB performed action X.",
        mock_response_content="Analysis complete: Found interesting patterns."
    )

@pytest.mark.asyncio
async def test_narrator_engine_main_loop_processes_one_event(
    initialized_narrator_engine: NarratorEngine, httpx_mock: HTTPXMock
):
    await _test_engine_main_loop_processes_one_event(
        engine=initialized_narrator_engine,
        httpx_mock=httpx_mock,
        event_prompt_key="prompt", # NarratorEngine expects 'prompt'
        sample_prompt="Describe the ancient, crumbling castle at dusk.",
        mock_response_content="The castle loomed, its ancient stones whispering tales of yore under the fading light."
    )

# TODO: Add tests for error handling (e.g., agent processing error, API errors)
# TODO: Add tests for multiple events in queue
# TODO: Add tests for engine state persistence via API (if implemented and used by main_loop)

