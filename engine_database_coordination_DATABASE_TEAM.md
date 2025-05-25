# Engine-Database Coordination Guide

This document outlines the interaction points between the engine system and database layer, serving as a coordination guide for the engine development and database teams.

## Engine Event Flow Analysis

### 1. Engine-Specific Events

#### ActorEngine
**Primary Triggers:**
- Character dialogue/action requests
- State updates from other agents
- Scene context changes

**Database Dependencies:**
- Character template data (`AgentTemplate` table)
- Current state/memory storage
- Interaction history (`EventInstance` table)

#### NarratorEngine
**Primary Triggers:**
- Scene initialization
- Environment state changes
- Character action outcomes

**Database Dependencies:**
- Scene templates (`ScenarioTemplate` table)
- World state storage
- Event flow configuration

#### AnalystEngine
**Primary Triggers:**
- Scenario completion events
- Pattern detection requests
- Real-time analysis triggers

**Database Dependencies:**
- Analysis templates
- Historical event data
- Pattern recognition rules

### 2. Required Processing Information

**Common Requirements for All Engines:**
```json
{
    "template_data": {
        "source": "AgentTemplate table",
        "required_fields": ["personality_config", "llm_config", "tools_config"]
    },
    "runtime_config": {
        "source": "ScenarioRun table",
        "includes": ["model_settings", "execution_parameters"]
    },
    "event_context": {
        "source": "EventInstance table",
        "includes": ["event_type", "data", "related_agents"]
    }
}
```

**Engine-Specific Requirements:**
```json
{
    "ActorEngine": {
        "character_profiles": "AgentTemplate.personality_config",
        "relationship_data": "ScenarioTemplate.agent_roles"
    },
    "NarratorEngine": {
        "scene_descriptions": "ScenarioTemplate.config",
        "world_rules": "ScenarioTemplate.event_flow"
    },
    "AnalystEngine": {
        "metrics_definitions": "ScenarioTemplate.config",
        "success_criteria": "ScenarioTemplate.config"
    }
}
```

### 3. Engine Output/Events

**Common Outputs:**
- Event records in `EventInstance` table
- State updates in `engine_states` table
- Execution logs in `execution_logs` table

**Specific Outputs:**
```json
{
    "ActorEngine": {
        "event_types": ["character_action", "dialogue", "state_change"],
        "data_structure": {
            "action": "string",
            "dialogue": "string",
            "metadata": "json"
        }
    },
    "NarratorEngine": {
        "event_types": ["scene_description", "environment_update", "narrative_intervention"],
        "data_structure": {
            "description": "string",
            "affected_elements": "json",
            "narrative_context": "json"
        }
    },
    "AnalystEngine": {
        "event_types": ["pattern_detected", "insight_generated", "recommendation"],
        "data_structure": {
            "analysis_type": "string",
            "findings": "json",
            "confidence": "float"
        }
    }
}
```

## Required Database Schema Updates

### 1. Event Type Enhancements
```sql
ALTER TABLE event_types 
    ADD COLUMN category VARCHAR(50),
    ADD COLUMN engine_type VARCHAR(50);
```

### 2. Event Flow Tracking
```sql
ALTER TABLE event_instances
    ADD COLUMN processed_by_engines JSON,
    ADD COLUMN priority INTEGER;
```

### 3. Engine State Storage
```sql
CREATE TABLE engine_states (
    id INTEGER PRIMARY KEY,
    engine_type VARCHAR(50),
    instance_id INTEGER,
    state JSON,
    updated_at TIMESTAMP,
    FOREIGN KEY (instance_id) REFERENCES scenario_runs(id)
);
```

## Integration Considerations

1. **Transaction Management:**
   - Each engine operation should be atomic
   - State updates must be synchronized
   - Event processing order must be maintained

2. **Error Handling:**
   - Failed events should be retried
   - State rollback mechanisms needed
   - Error logging for debugging

3. **Performance:**
   - Batch processing for multiple events
   - Efficient state storage/retrieval
   - Index optimization for common queries

## Next Steps

1. **Database Team:**
   - Implement schema updates
   - Create migration scripts
   - Optimize queries for common operations

2. **Engine Team:**
   - Implement state management
   - Add event processing logic
   - Integrate error handling

3. **Coordination Team:**
   - Define event priority system
   - Establish retry policies
   - Create monitoring strategy

## API Endpoints Needed

```python
# Event Management
POST /api/v1/events/
GET /api/v1/events/{event_id}
PUT /api/v1/events/{event_id}/process

# Engine State
GET /api/v1/engines/{engine_type}/state
PUT /api/v1/engines/{engine_type}/state

# Coordination
POST /api/v1/scenario/{scenario_id}/orchestrate
GET /api/v1/scenario/{scenario_id}/status
```

## Future Considerations

1. **Scaling:**
   - Event queue implementation
   - Load balancing between engines
   - State partitioning

2. **Monitoring:**
   - Engine performance metrics
   - Event processing statistics
   - Error rate tracking

3. **Recovery:**
   - State restoration procedures
   - Event replay capabilities
   - Consistency checks
