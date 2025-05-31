
# Full Scenario Run: Updated End-to-End Process

This document outlines the updated process for running a scenario in PyScrAI, reflecting the latest event-driven architecture and inter-agent communication system.

## 1. Prepare Templates in the Database
- Save your generic templates for actor, analyst, and narrator agents.
- Ensure the scenario template (for a conversation or analysis scenario) references the agent roles and their template names.

## 2. Start a Scenario Run
- Use the ScenarioRunner to launch a new scenario run by specifying the scenario template name.
- The system loads the template which defines:
    - Agent roles (e.g., Actor, Analyst, Narrator)
    - Event flow (sequence of actions and triggers)
    - Initial configuration or state

## 3. Create Agent Instances
For each agent role defined in the scenario template:
- The AgentFactory creates an agent instance from the corresponding agent template.
- Each instance is linked to the scenario run and configured with any runtime overrides.

## 4. Initialize Engines, Orchestration, and Scenario Context
- The EngineManager registers all agent instances and initializes the respective engines (ActorEngine, AnalystEngine, NarratorEngine).
- EngineManager stores scenario context in `scenario_context_data`, including event flow, agent roles, and turn management info.
- The system sets up the initial scenario state and triggers the first event in the event flow (e.g., “scenario_initialization”) by calling `deliver_event_to_agent` for the relevant agent(s).

## 5. Event-Driven Execution Pipeline
The pipeline now operates as follows:
- **Initialize agents**
- **Event loop:**
    - Agents publish standardized `agent.action.output` events to the EventBus when they complete an action.
    - EngineManager subscribes to these events and uses `_handle_agent_action_output` to interpret and route them according to the scenario's `event_flow`.
    - EngineManager determines the next target agent(s) and event type, then calls `deliver_event_to_agent` in AgentRuntime.
    - Each agent engine implements `handle_delivered_event` to process incoming events and trigger the next action.
- **Analyze results:** The analyst agent may provide summaries or evaluations.
- **Narrate/log outcomes:** The narrator agent may deliver commentary or summaries.
- **Cleanup:** Finalize the run.
    
This event-driven approach leverages the engines, event bus, EngineManager, and state manager for robust orchestration.

## 6. Agent Interactions, LLM Calls, and Event Routing
During the event loop:
- Agents generate actions or messages (with LLM support if needed).
- Each action is published as an `agent.action.output` event.
- EngineManager consults the scenario's `event_flow` to determine how to route each event to the next agent(s).
- Actions are processed and routed dynamically, enabling flexible and complex interaction patterns as defined in the scenario template.

## 7. Logging and State Updates
- All agent actions, LLM responses, and scenario state changes are logged in the database.
- The state manager maintains the current scenario and agent states.
- EngineManager manages turn-based scenarios by tracking the current turn holder in scenario context and validating turns before processing events.

## 8. Completion and Results
- The scenario run continues until a completion condition is met (e.g., all events processed or a goal reached).
- Final state and results are stored in the database.
- The run is marked as complete.

## 9. Review and API Access
- Review the run, logs, and results via the database or API endpoints.
- The system supports pausing, resuming, or analyzing completed runs.

### In Summary
- Define your agents and scenario in templates.
- Start a run, and the system automatically creates agent instances.
- EngineManager orchestrates all interactions using an event-driven pipeline, routing events between agents according to the scenario's event flow.
- Log and persist results in the database.
- Each agent (actor, analyst, narrator) fulfills its designated role in a managed, end-to-end process, with all communication and state changes coordinated by EngineManager.