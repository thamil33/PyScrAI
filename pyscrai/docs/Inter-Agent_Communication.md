### EngineManager Stores Rich Scenario Context 

-   In `EngineManager.__init__`, add `self.scenario_context_data: Dict[str, Dict[str, Any]] = {}`.
-   When a scenario starts (e.g., in `start_scenario_execution`), populate `self.scenario_context_data[scenario_run_id]` with:
    -   The parsed `event_flow` from `generic_conversation.json`.
    -   Agent role mappings (e.g., `agent_instance_id` -> `"primary_actor"`).
    -   Lists of agents by role for quick lookup.
    -   Initial turn information if applicable (e.g., who starts).

### Agents Publish Standardized "Action Output" Events (Hybrid)

-   Agents (their engines, like `ActorEngine`, `NarratorEngine` from `agent_runtime.py`) should use the `EventBus` (provided via `EngineManager`).
-   They publish a well-defined event when they complete an action relevant to the flow, e.g., `agent.action.output`.
-   Payload: `{ "scenario_run_id": int, "source_agent_id": int, "source_agent_role": str, "output_type": str (e.g., "message", "description", "analysis"), "data": Dict[str, Any] }`.

### EngineManager Subscribes, Interprets, and Routes (Plan B)

-   `EngineManager` subscribes to `agent.action.output` on the `EventBus`.
-   The callback is `async def _handle_agent_action_output(self, event_payload: Dict[str, Any])`.
-   Inside `_handle_agent_action_output`:
    -   Use `scenario_run_id` to get the context from `self.scenario_context_data`.
    -   Consult the `event_flow` based on `source_agent_role` and `output_type` to find the current step in the flow (e.g., `generic_conversation.json`'s `"conversation_turn"` or `"scene_setting"`).
    -   Determine target role(s) (e.g., `"other_actors"`, `"all_agents"`) and the next event type for the target(s) as per the `event_flow` definition.
    -   Identify specific target `agent_instance_id`(s).
    -   Transform the data from the agent's output into the payload required for the next event type.
    -   Dispatch to targets: Call a new method on `AgentRuntime` for each target: `await self.agent_runtime.deliver_event_to_agent(target_agent_id, next_event_type, transformed_payload)`. (This `deliver_event_to_agent` would be new in `agent_runtime.py` and would pass the event to the agent's engine's event handling method).

### Agent Engines Handle Delivered Events (Plan A & B)

-   Each engine (e.g., `BaseEngine`, `ActorEngine`) will need a method like `async def handle_delivered_event(self, event_type: str, payload: Dict[str, Any])`. This method processes the event and triggers the agent's response/next action.

### EngineManager Initiates Scenario Flow (Plan B)

-   `start_scenario_execution` should trigger the first event in the `event_flow` (e.g., `"scenario_initialization"`), by preparing its payload and calling `deliver_event_to_agent` for all relevant agents.
-   To "prompt" an agent (e.g., the narrator for `"scene_setting"`), `EngineManager` can send a specific directive event (e.g., type `"system.request_action"`) to that agent via `deliver_event_to_agent`. The agent's output would then flow back through `_handle_agent_action_output`.

### Turn Management (Plan B)

-   For `interaction_rules.turn_based = true`, `EngineManager` would update `self.scenario_context_data[scenario_run_id]['current_turn_holder']` after a valid turn, and `_handle_agent_action_output` would verify if the `source_agent_id` is the current turn holder before processing.

This refined approach, strongly guided by Plan B's event-flow-centric design, seems the most robust for your goals with `generic_conversation.json`. It makes `EngineManager` the central conductor of the scenario's narrative and interaction logic. The existing `queue_event` method in `engine_manager.py`, which writes to the DB and publishes, might be used for more durable, externally triggered, or asynchronous system events, while the internal agent-to-agent flow via `_handle_agent_action_output` can be more immediate.