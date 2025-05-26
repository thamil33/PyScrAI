"""
Tests for Pydantic schema validation
"""
import pytest
from datetime import datetime
from pyscrai.databases.models.schemas import (
    EngineRegistration,
    EngineHeartbeat,
    ResourceLimits,
    EventStatusUpdate
)

class TestSchemaValidation:
    """Test Pydantic schema validation"""
    
    def test_resource_limits_validation(self):
        """Test ResourceLimits schema validation"""
        # Valid data
        valid_limits = ResourceLimits(
            max_concurrent_events=5,
            memory_limit_mb=512
        )
        assert valid_limits.max_concurrent_events == 5
        assert valid_limits.memory_limit_mb == 512
        
        # Invalid data (should raise validation error)
        with pytest.raises(ValueError):
            ResourceLimits(max_concurrent_events=0)  # Should be > 0
        
        with pytest.raises(ValueError):
            ResourceLimits(max_concurrent_events=5, memory_limit_mb=-100)  # Should be > 0
    
    def test_engine_registration_validation(self):
        """Test EngineRegistration schema validation"""
        resource_limits = ResourceLimits(max_concurrent_events=3, memory_limit_mb=256)
        
        # Valid registration
        registration = EngineRegistration(
            engine_type="ActorEngine",
            capabilities=["dialogue", "character_interaction"],
            resource_limits=resource_limits
        )
        
        assert registration.engine_type == "ActorEngine"
        assert len(registration.capabilities) == 2
        
        # Invalid registration
        with pytest.raises(ValueError):
            EngineRegistration(
                engine_type="",  # Should have min_length=1
                capabilities=["dialogue"],
                resource_limits=resource_limits
            )
        
        with pytest.raises(ValueError):
            EngineRegistration(
                engine_type="ActorEngine",
                capabilities=[],  # Should have min_length=1
                resource_limits=resource_limits
            )
    
    def test_engine_heartbeat_validation(self):
        """Test EngineHeartbeat schema validation"""
        # Valid heartbeat
        heartbeat = EngineHeartbeat(
            status="active",
            current_workload=5,
            resource_utilization={
                "cpu_percent": 45.5,
                "memory_mb": 256.0
            }
        )
        
        assert heartbeat.status == "active"
        assert heartbeat.current_workload == 5
        assert heartbeat.resource_utilization["cpu_percent"] == 45.5
        
        # Invalid heartbeat
        with pytest.raises(ValueError):
            EngineHeartbeat(
                status="",  # Should have min_length=1
                current_workload=5
            )
        
        with pytest.raises(ValueError):
            EngineHeartbeat(
                status="active",
                current_workload=-1  # Should be >= 0
            )
    
    def test_event_status_update_validation(self):
        """Test EventStatusUpdate schema validation"""
        # Valid status update with result
        status_update = EventStatusUpdate(
            status="completed",
            result={"response": "Test response"},
            error=None
        )
        
        assert status_update.status == "completed"
        assert status_update.result["response"] == "Test response"
        
        # Valid status update with error
        error_update = EventStatusUpdate(
            status="failed",
            result=None,
            error="Processing failed due to timeout"
        )
        
        assert error_update.status == "failed"
        assert error_update.error == "Processing failed due to timeout"
        
        # Both result and error can be None
        simple_update = EventStatusUpdate(status="processing")
        assert simple_update.result is None
        assert simple_update.error is None

if __name__ == "__main__":
    pytest.main([__file__, "-v"])