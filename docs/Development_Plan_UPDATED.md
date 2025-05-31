# PyScrAI Stage II Development Plan (Updated)

## Overview
This document reflects the current priorities and next steps for PyScrAI, focusing on robust end-to-end scenario execution, agent communication, and system integration. It incorporates the latest design refinements and implementation guidance from the original plan and inter-agent communication blueprint.

---

## Stage II Objectives (Refined)
**Goal:** Achieve seamless scenario execution from template loading, agent instantiation, LLM-driven interactions, event routing, and database persistence, culminating in a retrievable, completed scenario.

### Success Criteria
- [ ] Load scenario template from database
- [ ] Create agent instances from agent templates
- [ ] Start scenario with multiple interacting agents
- [ ] Agents make real LLM calls and respond to each other
- [ ] All interactions logged to database
- [ ] Scenario runs to natural completion
- [ ] Results stored and retrievable via API

---

## Key Integration Steps

### 1. Template & Agent Integration
- Fix and verify `create_scenario_run_from_template()` and `create_agent_instance()` methods.
- Ensure agent templates are correctly mapped to engine types (Actor/Narrator/Analyst).
- Guarantee templates load from the database and engines receive proper configuration.

### 2. Engine Factory & Specialized Engines
- Update `create_agent_engine()` to instantiate the correct engine class for each agent.
- Ensure engines are initialized with the right configuration and context.

### 3. Scenario Runner & Orchestration
- Integrate `ScenarioRunner` with `ScenarioFactory` and database.
- Ensure agents are created, started, and tracked properly.
- Persist scenario state and agent actions.

### 4. Inter-Agent Communication & Event Flow (Plan B)
- Implement `EngineManager` as the central conductor:
  - Store scenario context in `self.scenario_context_data`.
  - On scenario start, populate context with event flow, agent roles, and turn info.
- Agents publish standardized `agent.action.output` events to the `EventBus`.
- `EngineManager` subscribes to these events and routes them according to the scenario's `event_flow`:
  - Use `_handle_agent_action_output` to interpret and dispatch events.
  - Use `deliver_event_to_agent` to send events to target agents.
- Each engine implements `handle_delivered_event` to process incoming events and trigger agent actions.
- Manage turn-based scenarios by tracking and updating the current turn holder in context.

### 5. LLM & Memory Integration
- Update all engines to use the native LLM system.
- Add prompt engineering templates and conversation memory/context for each engine type.

### 6. Database Logging & API
- Log all agent interactions, LLM requests/responses, and scenario state changes.
- Implement scenario execution endpoints and real-time status monitoring in the API.

### 7. Testing & Demo
- Create and run integration tests for end-to-end scenario execution.
- Develop a demo script to showcase scenario flow, agent interactions, and database results.

---

## Implementation Order (Recommended)
1. Complete/fix agent and scenario template integration.
2. Implement and test inter-agent event routing in `EngineManager`.
3. Update engines for LLM and memory integration.
4. Ensure all actions and state changes are logged to the database.
5. Expand API for scenario execution and monitoring.
6. Write and run integration tests and demo scripts.

---

**This document supersedes previous plans for Stage II integration and should be used as the primary reference for ongoing development.**
