# PyScrAI Project Sync State - 2025-05-25

This document provides a snapshot of the PyScrAI project's development status, intended to help synchronize context, especially when paired with a fresh import of the GitHub repository.

## 1. Project Goal

PyScrAI (Python Scenario-based AI) aims to be a flexible and extensible framework for creating, running, and analyzing multi-agent AI simulations in dynamic environments. It leverages the Agno framework for underlying agent capabilities.

## 2. Current Development Phase

We are primarily focused on **Phase 2: Engine Implementation** as outlined in the `blueprint.md`. The objective is to create Agno agent wrappers for specialized roles within the simulation environment.

## 3. Engine Development Status

The initial structures for the core PyScrAI engines have been implemented:

* **`BaseEngine` (`pyscrai/engines/base_engine.py`)**:
    * Conceptualized and implemented as the foundational class for all specialized engines.
    * Includes common functionalities like `engine_id`, `engine_name`, basic state management (`get_state`, `load_state`), and logging.
* **`ActorEngine` (`pyscrai/engines/actor_engine.py`)**:
    * Initial implementation created, inheriting from `BaseEngine`.
    * Focuses on character simulation, incorporating `personality_traits` and `character_name`.
    * Its Agno agent's system message is configured to reflect these personality aspects.
* **`NarratorEngine` (`pyscrai/engines/narrator_engine.py`)**:
    * Initial implementation created, inheriting from `BaseEngine`.
    * Focuses on world-building, scene description, and narrative context.
    * Its Agno agent's system message is configured based on a defined `narrative_style`.
* **`AnalystEngine` (`pyscrai/engines/analyst_engine.py`)**:
    * Initial implementation created, inheriting from `BaseEngine`.
    * Focuses on result analysis and pattern detection.
    * Its Agno agent's system message is configured based on an `analytical_focus` to guide its interpretation of provided data.

## 4. Database Coordination Summary

Significant progress has been made in coordinating with the Database Team. Key decisions and plans include:

* **Seed Data Strategy**:
    * A hybrid approach was adopted:
        * `pyscrai/templates/` will continue to be used for user-facing Agent and Scenario *templates* (loaded by `setup_database.py`).
        * `pyscrai/databases/seeds/` will be used for core, non-template master data (e.g., predefined `EventType` definitions), with `setup_database.py` being refined to load these.
* **Schema and API Refinements** (based on `Database_Team_Communication.md` and Engine Team feedback like `Engine_Team_Response_To_DB_Plan_May_25.md`):
    * **`engine_states` Table**:
        * Will use a unique `engine_id UUID` as the primary/unique key.
        * The `metadata` JSON field will have a nested structure for `static_config` (capabilities, resource_limits, engine_software_version) and `dynamic_state` (resource_utilization, current_scenario_run_id).
    * **`event_instances` Table**:
        * The `processed_by_engines` JSON field will store an array of objects, each detailing an engine's processing attempt (`engine_id`, `engine_type`, `status`, `timestamp`, `retry_count`, `error`).
    * **Event Queue Implementation**:
        * Default batch size of 3-5 events (configurable via API `limit` parameter).
        * Event locking mechanism with a configurable visibility timeout (default 5 minutes suggested).
        * Event status values: "queued", "processing", "completed", "failed".
        * Lock format: "processing\_by\_\{engine\_id\}".
    * **Retry Policy**:
        * A comprehensive JSON structure for global retry policy is defined (max\_retries, initial/max delay, multiplier, dead\_letter\_threshold).
        * The Engine Team suggested that while a global policy is fine for now, future enhancements might include per-event-type retry configurations.
    * **Dead Letter Queue (DLQ)**:
        * Events reaching max retries will go to a DLQ (or marked as "dead\_letter").
        * A separate API for DLQ management (list, inspect, re-queue, delete) was strongly recommended by the Engine Team and seems to be a direction the Database Team is considering.
    * **API Endpoints**:
        * Refined endpoints for engine instance management (using `engine_id`):
            * `POST /api/v1/engine-instances/` (for registration; payload to be fully defined)
            * `GET /api/v1/engine-instances/{engine_id}/state`
            * `PUT /api/v1/engine-instances/{engine_id}/state`
            * `PUT /api/v1/engine-instances/{id}/heartbeat`
        * Refined event processing endpoints:
            * `GET /api/v1/events/queue/{engine_type}?limit=N`
            * `PUT /api/v1/events/{id}/status` (Engine Team confirmed payload should align with `processed_by_engines` structure)
            * `POST /api/v1/events/`
* **Current Database Team Focus**: Alembic integration for schema updates.

## 5. Next Immediate Focus for Engine Team & Framework Development

With the database interface and event handling mechanisms becoming more concrete, the Engine Team will now focus on:

* **Detailed Event Structure Definition:**
    * Defining common fields for all PyScrAI events (e.g., `event_id`, `event_type`, `timestamp`, `source_engine_id`, `target_engine_id/type`, `scenario_run_id`, `priority`, `payload`).
    * Creating Pydantic models for the `payload` of key event types generated and consumed by each engine.
* **Event Flow and Orchestration Logic:**
    * Designing how a `ScenarioManager` (or central orchestrator) initiates scenarios and manages the overall event flow.
    * Deciding on the responsibility for creating subsequent events:
        * Do engines directly `POST` new events after processing?
        * Or do engines return structured results, and the Orchestrator creates new events based on these results and scenario logic?
    * Defining strategies for event targeting (to specific engine instances or types) and handling broadcast events.
* **Engine Integration with Database APIs:**
    * Implementing the logic within `BaseEngine` (and specialized engines) to:
        * Poll for events from `GET /api/v1/events/queue/{engine_type}`.
        * Update event status via `PUT /api/v1/events/{id}/status`.
        * Manage and persist their state using `PUT /api/v1/engine-instances/{engine_id}/state`.
        * Handle registration (`POST /api/v1/engine-instances/`) and heartbeats (`PUT /api/v1/engine-instances/{id}/heartbeat`) as per `Engine_Team_Communication.md`.
* **Error Handling within Engines:** Refining how engines report errors for the retry and DLQ mechanisms