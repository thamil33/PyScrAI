# Database Team Response to Engine Team Feedback

Thank you for the comprehensive feedback! We're ready to move forward with implementation based on your responses.

## Implementation Plan

### 1. Engine States Metadata Structure
We'll implement the metadata JSON structure as suggested:

```json
{
    "static_config": {
        "capabilities": ["capability1", "capability2"],
        "resource_limits": {
            "max_concurrent_events": 5,
            "memory_limit_mb": 1024
        },
        "engine_software_version": "1.0.0"
    },
    "dynamic_state": {
        "resource_utilization": {
            "cpu_percent": 45.2,
            "memory_usage_mb": 512
        },
        "current_scenario_run_id": "uuid-here" // Optional, based on engine type
    }
}
```

### 2. Event Queue Implementation
We'll implement the following features:

1. Default batch size of 3 events with configurable limit parameter
2. Event locking mechanism with visibility timeout:
   - New status values: "queued", "processing", "completed", "failed"
   - Visibility timeout of 5 minutes (configurable)
   - Lock format: "processing_by_{engine_id}"

### 3. Retry Policy
Proposed retry mechanism:
```json
{
    "max_retries": 3,
    "retry_delay": {
        "initial": 30,  // seconds
        "max": 300,     // seconds
        "multiplier": 2 // exponential backoff
    },
    "dead_letter_threshold": 3
}
```

## Next Steps and Timeline

1. Immediate Tasks (This Week):
   - Create Alembic migration for schema updates
   - Implement event locking mechanism
   - Add retry policy configuration

2. API Implementation (Next Week):
   - Engine instance registration/heartbeat endpoints
   - Event queue endpoints with locking
   - Status update endpoints with retry logic

3. Testing and Documentation:
   - Unit tests for queue mechanics
   - Integration tests for engine-db interaction
   - API documentation updates

## Questions for Engine Team

1. Configuration Parameters:
   - Is 5 minutes a reasonable visibility timeout?
   - Should retry delays be configurable per event type?

2. Dead Letter Handling:
   - How should we handle events that reach max retries?
   - Should we implement a separate API for dead letter queue management?

Please review this implementation plan and let us know if any adjustments are needed before we begin the database updates.