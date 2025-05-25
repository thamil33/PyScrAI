"""
Tests for engine API endpoints
"""
import uuid
from datetime import datetime, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from pyscrai.databases.api.main import app
from pyscrai.databases.models.engine_models import EngineState
from pyscrai.databases.models.event_models import EventType, EventInstance
from pyscrai.databases.database import get_db


@pytest.fixture
def test_client():
    return TestClient(app)


@pytest.fixture
def db_session(test_db_session: Session) -> Session:
    """Fixture that provides a database session"""
    return test_db_session


@pytest.fixture(autouse=True)
def setup_test_db(test_db_session: Session):
    """Setup test database dependency override"""
    app.dependency_overrides[get_db] = lambda: test_db_session
    yield
    app.dependency_overrides = {}


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
        engine_metadata={
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
    # First try to get existing event type
    event_type = db_session.query(EventType).filter_by(name="test_event").first()
    if event_type is not None:
        return event_type

    # Create new event type if it doesn't exist
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
        scenario_run_id=1,  # Example scenario run ID
        source_agent_id=1,  # Example source agent ID
        status="queued",
        priority=1,
        data={"test": "data"},
        created_at=datetime.utcnow(),
        processed_by_engines=[]
    )
    db_session.add(event)
    db_session.commit()
    db_session.refresh(event)
    return event


class TestEngineAPI:
    """Test suite for engine API endpoints"""
    def test_register_engine(self, test_client: TestClient, sample_engine_registration):
        """Test engine registration endpoint"""
        response = test_client.post("/api/v1/engine-instances", json=sample_engine_registration)
        assert response.status_code == 200
        data = response.json()
        assert data["engine_type"] == sample_engine_registration["engine_type"]
        assert data["status"] == "active"
        assert "id" in data and uuid.UUID(data["id"])  # Valid UUID
        assert datetime.fromisoformat(data["last_heartbeat"])  # Valid timestamp
        assert data["engine_metadata"]["static_config"]["capabilities"] == sample_engine_registration["capabilities"]
        assert data["current_workload"] == 0  # Initial workload

    def test_heartbeat_update(self, test_client: TestClient, sample_engine, db_session: Session):
        """Test engine heartbeat update endpoint"""
        # Get initial heartbeat time
        initial_heartbeat = sample_engine.last_heartbeat
        
        heartbeat_data = {
            "status": "busy",
            "current_workload": 3,
            "resource_utilization": {
                "cpu_percent": 75.5,
                "memory_percent": 60.2
            }
        }
        
        # Wait a moment to ensure timestamp changes
        import time
        time.sleep(0.1)
        
        response = test_client.put(f"/api/v1/engine-instances/{sample_engine.id}/heartbeat", json=heartbeat_data)
        assert response.status_code == 200
        data = response.json()
        
        # Check all updated fields
        assert data["status"] == "busy"
        assert data["current_workload"] == 3
        assert data["engine_metadata"]["dynamic_state"]["resource_utilization"] == heartbeat_data["resource_utilization"]
        
        # Verify heartbeat was updated
        new_heartbeat = datetime.fromisoformat(data["last_heartbeat"])
        assert new_heartbeat > initial_heartbeat
        
        # Verify in database
        engine = db_session.query(EngineState).filter(EngineState.id == sample_engine.id).first()
        assert engine.status == "busy"
        assert engine.current_workload == 3

    def test_deregister_engine(self, test_client: TestClient, sample_engine, db_session: Session):
        """Test engine deregistration endpoint"""
        response = test_client.delete(f"/api/v1/engine-instances/{sample_engine.id}")
        assert response.status_code == 200
        assert response.json()["status"] == "success"

        # Verify engine is removed from database
        engine = db_session.query(EngineState).filter(EngineState.id == sample_engine.id).first()
        assert engine is None

    def test_register_engine_invalid_data(self, test_client: TestClient):
        """Test engine registration with invalid data"""
        invalid_data = {
            "engine_type": "",  # Empty engine type
            "capabilities": []  # Empty capabilities
        }
        response = test_client.post("/api/v1/engine-instances", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_heartbeat_nonexistent_engine(self, test_client: TestClient):
        """Test heartbeat update for non-existent engine"""
        fake_id = str(uuid.uuid4())
        heartbeat_data = {
            "status": "active",
            "current_workload": 0,
            "resource_utilization": {}
        }
        response = test_client.put(f"/api/v1/engine-instances/{fake_id}/heartbeat", json=heartbeat_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_events_queue(
        self,
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
        self,
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

    def test_event_retry_mechanism(
        self,
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
            f"/api/v1/events/queue/{sample_event.event_type.engine_type}",
            params={"engine_type": sample_event.event_type.engine_type}
        )
        events = response.json()
        assert len(events) == 1
        assert events[0]["retry_count"] == 1

    def test_event_max_retries(
        self,
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
            f"/api/v1/events/queue/{sample_event.event_type.engine_type}",
            params={"engine_type": sample_event.event_type.engine_type}
        )
        events = response.json()
        assert len(events) == 0

        # Verify event final status
        event = db_session.query(EventInstance).filter_by(id=sample_event.id).first()
        assert event.status == "failed"
        assert event.retry_count == 3
