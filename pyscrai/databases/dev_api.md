# PyScrAI API Developer Guide

This guide provides a concise overview for interacting with the PyScrAI API during development.

---

## 1. Start the API Server

1. **Activate the virtual environment:**
2. **Navigate to the project root (if needed):**
   cd C:\Users\tyler\dev\PyScrAI

---
3. **Start the API server:**

  uvicorn pyscrai.databases.api.main:app --reload
 
---
## 2. API Documentation

# Automatically creates and outputs html site project documentation
pdoc --html ./pyscrai -o ./pyscrai_docs

- Visit [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the interactive Swagger UI.
- All endpoints are grouped under:
  - `/api/v1/engines` (engine management, event queue)
  - `/api/v1/scenarios` (scenario runs, events)
  - `/api/v1/templates` (agent/scenario templates)

---

## 3. Example API Interactions

### Register an Engine
```http
POST /api/v1/engines/register
Content-Type: application/json
{
  "engine_type": "actor",
  "engine_id": "engine-001",
  "capabilities": { ... },
  "resource_limits": { ... },
  "metadata": { ... }
}
```

### Request Events for Processing
```http
POST /api/v1/engines/queue/request
Content-Type: application/json
{
  "engine_id": "engine-001",
  "engine_type": "actor",
  "max_events": 5
}
```

### Update Event Status
```http
PUT /api/v1/engines/events/{event_id}/status
Content-Type: application/json
{
  "status": "completed",
  "result": { ... }
}
```

### Create a Scenario Run
```http
POST /api/v1/scenarios/run
Content-Type: application/json
{
  "template_id": 1,
  "run_name": "test_run_001"
}
```



## CRUD - Create - Read - Update - Delete 

### 1. Create
**What:** Add a new resource (e.g., agent template, scenario template, scenario run).  
**How:** Use an HTTP POST request.  

**Example:** Include the new resource in the request body.

POST /api/v1/templates/agent
Content-Type: application/json
{
{
  "name": "Generic Conversation",
  "description": "A flexible conversation scenario that can be adapted for various interaction types",
  "config": {
    "max_turns": 20,
    "timeout_seconds": 3600,
    "completion_conditions": {
      "natural_conclusion": true,
      "max_turns_reached": true,
      "timeout_reached": true
    },
    "error_handling": {
      "retry_attempts": 3,
      "fallback_responses": true,
      "graceful_degradation": true
    },
    "interaction_rules": {
      "turn_based": true,
      "allow_interruptions": false,
      "require_responses": true
    }
  },
  "agent_roles": {
    "primary_actor": {
      "template_name": "Generic Actor",
      "role_config": {
        "role": "main_participant",
        "description": "Primary participant in the conversation",
        "interaction_priority": "high"
      },
      "required": true,
      "engine_type": "actor"
    },
    "secondary_actor": {
      "template_name": "Generic Actor", 
      "role_config": {
        "role": "secondary_participant",
        "description": "Secondary participant in the conversation",
        "interaction_priority": "medium"
      },
      "required": false,
      "engine_type": "actor"
    },
    "narrator": {
      "template_name": "Generic Narrator",
      "role_config": {
        "role": "scene_setter",
        "description": "Provides context and scene descriptions",
        "interaction_priority": "low"
      },
      "required": false,
      "engine_type": "narrator"
    },
    "analyst": {
      "template_name": "Generic Analyst",
      "role_config": {
        "role": "observer",
        "description": "Analyzes conversation dynamics and provides insights",
        "interaction_priority": "background"
      },
      "required": false,
      "engine_type": "analyst"
    }
  },
  "event_flow": {
    "scenario_initialization": {
      "type": "trigger",
      "source": "system",
      "target": "all_agents",
      "data_schema": {
        "scenario_context": "string",
        "initial_setting": "object",
        "participant_roles": "object"
      },
      "conditions": {
        "trigger": "scenario_start",
        "required": true
      }
    },
    "scene_setting": {
      "type": "state_change",
      "source": "narrator",
      "target": "all_agents",
      "data_schema": {
        "scene_description": "string",
        "atmosphere": "string",
        "context_details": "object"
      },
      "conditions": {
        "trigger": "initialization_complete",
        "required_if": "narrator_present"
      }
    },
    "conversation_turn": {
      "type": "interaction",
      "source": "any_actor",
      "target": "other_actors",
      "data_schema": {
        "message": "string",
        "intent": "string",
        "emotional_state": "string"
      },
      "conditions": {
        "trigger": "previous_turn_complete",
        "repeatable": true,
        "max_iterations": "config.max_turns"
      }
    },
    "analysis_checkpoint": {
      "type": "state_change",
      "source": "analyst",
      "target": "system",
      "data_schema": {
        "interaction_metrics": "object",
        "behavioral_insights": "array",
        "scenario_health": "string"
      },
      "conditions": {
        "trigger": "every_n_turns",
        "n": 5,
        "required_if": "analyst_present"
      }
    },
    "scenario_conclusion": {
      "type": "trigger",
      "source": "system",
      "target": "all_agents",
      "data_schema": {
        "conclusion_reason": "string",
        "final_state": "object",
        "summary": "string"
      },
      "conditions": {
        "trigger": "completion_condition_met",
        "final": true
      }
    }
  },
  "runtime_customization": {
    "agent_personalities": "configurable",
    "conversation_topic": "configurable",
    "interaction_style": "configurable",
    "completion_criteria": "configurable"
  }
}
}


### 2. Read
**What:** Retrieve one or more resources.  
**How:** Use an HTTP GET request.  
**Examples:**  
- GET /api/v1/templates (returns a list of templates)  
- GET /api/v1/templates/{template_id} (returns one template)

### 3. Update
**What:** Modify an existing resource.  
**How:** Use an HTTP PUT or PATCH request.  

**Example:** Send updated fields in the request body.

PUT /api/v1/templates/agent/{template_id}
Content-Type: application/json
{
  "description": "Updated description"
}

### 4. Delete
**What:** Remove a resource.  
**How:** Use an HTTP DELETE request.  

**Example:** Specify the resource ID in the path.

DELETE /api/v1/templates/agent/{template_id}

**Summary**  
- Create: POST  
- Read: GET  
- Update: PUT or PATCH  
- Delete: DELETE
---

---

**Happy developing with PyScrAI!**
