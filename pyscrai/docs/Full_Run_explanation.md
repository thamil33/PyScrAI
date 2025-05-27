# Full Run Explanation

This document outlines the process for running a scenario using agent templates and a scenario template stored in the database.

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

## 4. Initialize Engines and Orchestration
- The EngineManager registers all agent instances and initializes the respective engines (ActorEngine, AnalystEngine, NarratorEngine).
- The system sets up the initial scenario state and queues any preliminary events (e.g., “start conversation”).

## 5. Run the Execution Pipeline
The pipeline executes the following steps:
- **Initialize agents**
- **Run event loop:** Agents take turns processing events and interacting.
- **Analyze results:** The analyst agent may provide summaries or evaluations.
- **Narrate/log outcomes:** The narrator agent may deliver commentary or summaries.
- **Cleanup:** Finalize the run.
    
Each step leverages the engines, event bus, and state manager.

## 6. Agent Interactions and LLM Calls
During the event loop:
- The actor agent may generate actions or messages (with LLM support if needed).
- The analyst agent evaluates the actor’s output or scenario state.
- The narrator agent offers commentary or summaries.
    
Actions are processed and routed as defined in the scenario template.

## 7. Logging and State Updates
- All agent actions, LLM responses, and scenario state changes are logged in the database.
- The state manager maintains the current scenario and agent states.

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
- Orchestrate interactions using engines and pipelines.
- Log and persist results in the database.
- Each agent (actor, analyst, narrator) fulfills its designated role in a managed, end-to-end process.