# Inter-Agent Communication System (Updated Design)

## Overview
This document details the updated design for inter-agent communication and event routing in PyScrAI, based on the latest integration plan and scenario requirements.

---

## EngineManager: Scenario Context & Event Flow
- `EngineManager` maintains `self.scenario_context_data: Dict[str, Dict[str, Any]]`.
- On scenario start, context is populated with:
  - Parsed `event_flow` from the scenario template.
  - Agent role mappings (e.g., `agent_instance_id` → `role_name`).
  - Lists of agents by role for quick lookup.
  - Turn management info if applicable.

## Agent Output Events
- Agents (via their engines) publish standardized `agent.action.output` events to the `EventBus`.
- Event payload example:
  ```python
  {
    "scenario_run_id": int,
    "source_agent_id": int,
    "source_agent_role": str,
    "output_type": str,  # e.g., "message", "description", "analysis"
    "data": dict
  }
  ```

## EngineManager Event Routing
- `EngineManager` subscribes to `agent.action.output` events.
- Handler: `async def _handle_agent_action_output(self, event_payload: Dict[str, Any])`
- Steps:
  1. Retrieve scenario context using `scenario_run_id`.
  2. Consult `event_flow` to determine the next step based on `source_agent_role` and `output_type`.
  3. Identify target role(s) and event type for the next step.
  4. Map target roles to specific `agent_instance_id`(s).
  5. Transform the output data as needed for the next event.
  6. Dispatch to targets using `await self.agent_runtime.deliver_event_to_agent(target_agent_id, next_event_type, transformed_payload)`.

## Agent Engine Event Handling
- Each engine implements:
  ```python
  async def handle_delivered_event(self, event_type: str, payload: dict)
  ```
- This method processes incoming events and triggers the agent's next action.

## Scenario Flow Initiation
- `EngineManager.start_scenario_execution` triggers the first event in the `event_flow`.
- Uses `deliver_event_to_agent` to prompt the appropriate agent(s) to begin the scenario.

## Turn Management
- For turn-based scenarios, `EngineManager` tracks the current turn holder in context.
- `_handle_agent_action_output` checks turn validity before processing.

---

## Implementation Checklist
- [ ] Store and manage scenario context in `EngineManager`.
- [ ] Standardize agent output events and publish to `EventBus`.
- [ ] Implement event routing logic in `_handle_agent_action_output`.
- [ ] Implement `deliver_event_to_agent` in `AgentRuntime`.
- [ ] Implement `handle_delivered_event` in all agent engines.
- [ ] Initiate scenario flow and manage turns as needed.

---

## References
- See original `docs/Inter-Agent_Communication.md` for legacy details.
- Use this document as the authoritative reference for inter-agent event flow and communication logic.
