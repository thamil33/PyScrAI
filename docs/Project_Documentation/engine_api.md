# Engine API Documentation

## Overview
The Engine API provides endpoints for managing engine instances and event processing in the PyScrAI system. It enables registration of processing engines, event queue management, and status tracking.

## Engine Management

### Register Engine Instance
```http
POST /api/v1/engine-instances
```

Register a new engine instance in the system.

**Request Body:**
```json
{
    "engine_type": "actor",
    "capabilities": ["dialogue_generation", "character_simulation"],
    "resource_limits": {
        "max_concurrent_events": 5,
        "memory_limit_mb": 1024
    }
}
```

**Response:**
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "engine_type": "actor",
    "status": "active",
    "last_heartbeat": "2024-05-25T10:00:00Z",
    "current_workload": 0,
    "metadata": {
        "static_config": {
            "capabilities": ["dialogue_generation", "character_simulation"],
            "resource_limits": {
                "max_concurrent_events": 5,
                "memory_limit_mb": 1024
            }
        },
        "dynamic_state": {
            "resource_utilization": {}
        }
    }
}
```

### Update Engine Heartbeat
```http
PUT /api/v1/engine-instances/{engine_id}/heartbeat
```

Update the status and heartbeat of an engine instance.

**Request Body:**
```json
{
    "status": "processing",
    "current_workload": 2,
    "resource_utilization": {
        "cpu_percent": 45.2,
        "memory_usage_mb": 512
    }
}
```

## Event Processing

### Get Events for Processing
```http
GET /api/v1/events/queue/{engine_type}
```

Retrieve the next batch of events for processing.

**Query Parameters:**
- `batch_size` (optional): Number of events to retrieve (default: 3, max: 10)

**Response:**
```json
[
    {
        "id": 123,
        "event_type_id": 456,
        "event_type": "character_dialogue",
        "priority": 1,
        "data": {
            "character_id": "789",
            "message": "Hello world!"
        },
        "lock_until": "2024-05-25T10:05:00Z",
        "retry_count": 0
    }
]
```

### Update Event Status
```http
PUT /api/v1/events/{event_id}/status
```

Update the processing status of an event.

**Request Body:**
```json
{
    "status": "completed",
    "result": {
        "response": "Hello there!",
        "confidence": 0.95
    }
}
```

## Error Handling

### Status Codes
- 200: Successful operation
- 400: Bad request (invalid input)
- 404: Resource not found
- 409: Conflict (e.g., duplicate registration)
- 500: Internal server error

### Retry Policy
- Maximum 3 retry attempts
- Exponential backoff: 30s, 60s, 120s
- Failed events after max retries are moved to dead letter queue

## Running the API Server

Start the API server using uvicorn:

```powershell
cd C:\Users\tyler\dev\PyScrAI
uvicorn pyscrai.databases.api.app:app --reload --port 8000
```

The API documentation will be available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
