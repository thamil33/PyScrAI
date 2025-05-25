"""
Tests for engine API endpoints
"""
import uuid
from datetime import datetime, timedelta
from typing import AsyncGenerator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from ..api.app import app
from ..models.engine_models import EngineState
from ..models.event_models import EventType, EventInstance
from ..database import get_db


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def db_session(test_db_session: Session) -> Session:
    """Fixture that provides a database session"""
    return test_db_session


def override_get_db(test_db_session: Session):
    """Override database dependency for testing"""
    try:
        yield test_db_session
    finally:
        test_db_session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def sample_engine_registration():
    """Sample data for engine registration"""
    return {
        "engine_type": "actor",
        "capabilities": ["dialogue_generation", "character_simulation"],
        "resource_limits": {
            "max_concurrent_events": 5,
            "memory_limit_mb": 1024
        }
    }


@pytest.fixture
def sample_engine(db_session: Session) -> EngineState:
    """Create a sample engine instance in the database"""
    engine = EngineState(
        id=str(uuid.uuid4()),
        engine_type="actor",
        status="active",
        last_heartbeat=datetime.utcnow(),
        current_workload=0,
        metadata={
            "static_config": {
                "capabilities": ["dialogue_generation"],
                "resource_limits": {"max_concurrent_events": 5}
            },
            "dynamic_state": {
                "resource_utilization": {}
            }
        }
    )
    db_session.add(engine)
    db_session.commit()
    db_session.refresh(engine)
    return engine


@pytest.fixture
def sample_event_type(db_session: Session) -> EventType:
    """Create a sample event type in the database"""
    event_type = EventType(
        name="test_event",
        description="Test event for engine processing",
        engine_type="actor",
        category="test",
        data_schema={"type": "object", "properties": {}}
    )
    db_session.add(event_type)
    db_session.commit()
    db_session.refresh(event_type)
    return event_type


@pytest.fixture
def sample_event(db_session: Session, sample_event_type: EventType) -> EventInstance:
    """Create a sample event instance in the database"""
    event = EventInstance(
        event_type_id=sample_event_type.id,
        status="queued",
        priority=1,
        data={"test": "data"},
        created_at=datetime.utcnow()
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


def test_register_engine(test_client: TestClient, sample_engine_registration: dict):
    """Test engine registration endpoint"""
    response = test_client.post("/api/v1/engine-instances", json=sample_engine_registration)
    assert response.status_code == 200
    data = response.json()
    assert data["engine_type"] == sample_engine_registration["engine_type"]
    assert data["status"] == "active"
    assert "id" in data
    assert isinstance(data["id"], str)


def test_update_heartbeat(
    test_client: TestClient,
    sample_engine: EngineState
):
    """Test engine heartbeat update endpoint"""
    heartbeat_data = {
        "status": "processing",
        "current_workload": 2,
        "resource_utilization": {
            "cpu_percent": 45.2,
            "memory_usage_mb": 512
        }
    }
    response = test_client.put(
        f"/api/v1/engine-instances/{sample_engine.id}/heartbeat",
        json=heartbeat_data
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert data["current_workload"] == 2


def test_deregister_engine(
    test_client: TestClient,
    sample_engine: EngineState
):
    """Test engine deregistration endpoint"""
    response = test_client.delete(f"/api/v1/engine-instances/{sample_engine.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify engine is actually deleted
    response = test_client.put(
        f"/api/v1/engine-instances/{sample_engine.id}/heartbeat",
        json={"status": "active", "current_workload": 0}
    )
    assert response.status_code == 404


def test_get_events_queue(
    test_client: TestClient,
    sample_engine: EngineState,
    sample_event: EventInstance,
    sample_event_type: EventType
):
    """Test getting events from the queue"""
    request_data = {
        "engine_type": sample_event_type.engine_type,
        "batch_size": 5,
        "capabilities": ["dialogue_generation"]
    }
    response = test_client.get(
        f"/api/v1/events/queue/{sample_event_type.engine_type}",
        params=request_data
    )
    assert response.status_code == 200
    events = response.json()
    assert len(events) > 0
    assert events[0]["id"] == sample_event.id
    assert events[0]["event_type_id"] == sample_event_type.id
    assert "lock_until" in events[0]


def test_update_event_status(
    test_client: TestClient,
    sample_event: EventInstance
):
    """Test updating event status"""
    status_update = {
        "status": "completed",
        "result": {"response": "Test completed successfully"},
        "error": None
    }
    response = test_client.put(
        f"/api/v1/events/{sample_event.id}/status",
        json=status_update
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify event status is updated
    response = test_client.get(
        f"/api/v1/events/queue/{sample_event.event_type.engine_type}"
    )
    events = response.json()
    assert len(events) == 0  # Event should not be in queue anymore


def test_event_retry_mechanism(
    test_client: TestClient,
    sample_event: EventInstance
):
    """Test event retry mechanism on failure"""
    # Fail the event
    status_update = {
        "status": "failed",
        "result": None,
        "error": "Test error"
    }
    response = test_client.put(
        f"/api/v1/events/{sample_event.id}/status",
        json=status_update
    )
    assert response.status_code == 200

    # Verify event is requeued with retry count
    response = test_client.get(
        f"/api/v1/events/queue/{sample_event.event_type.engine_type}"
    )
    events = response.json()
    assert len(events) == 1
    assert events[0]["retry_count"] == 1


def test_event_max_retries(
    test_client: TestClient,
    sample_event: EventInstance,
    db_session: Session
):
    """Test event reaches max retries"""
    # Fail the event multiple times
    for _ in range(3):
        status_update = {
            "status": "failed",
            "result": None,
            "error": "Test error"
        }
        response = test_client.put(
            f"/api/v1/events/{sample_event.id}/status",
            json=status_update
        )
        assert response.status_code == 200

    # Verify event is not in queue after max retries
    response = test_client.get(
        f"/api/v1/events/queue/{sample_event.event_type.engine_type}"
    )
    events = response.json()
    assert len(events) == 0

    # Verify event final status
    event = db_session.query(EventInstance).filter_by(id=sample_event.id).first()
    assert event.status == "failed"
    assert event.retry_count == 3
