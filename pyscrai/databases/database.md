# PyScrAI Database Development: Next Steps

This document outlines the immediate next steps for PyScrAI database development, focusing on completing Phase 1 deliverables and preparing for subsequent phases as described in `blueprint.md`.

---

## 1. Refine SQLAlchemy Model Relationships and Constraints

**Objective:** Ensure data integrity and proper ORM behavior.

**Tasks:**
- Review all `relationship()` definitions in SQLAlchemy models (`pyscrai/databases/models/*.py`).
- Verify `back_populates` are correctly configured for bidirectional relationships.
- Define appropriate cascade options (e.g., `all`, `delete-orphan`) for related objects, especially for `ScenarioRun` and its associated `AgentInstance`, `EventInstance`, and `ExecutionLog` records.
- Identify and add any missing database-level constraints (e.g., `UniqueConstraint`, `CheckConstraint`) to enforce data rules beyond basic `nullable` and `unique` column properties.

---

## 2. Implement Database Migrations with Alembic

**Objective:** Enable robust schema evolution and management.

**Tasks:**
- Integrate Alembic into the project.
- Initialize Alembic within the `pyscrai/databases/` directory.
- Configure Alembic to work with existing SQLAlchemy models and database connection.
- Generate an initial migration script based on the current state of the models.
- Update `setup_database.py` or document the workflow to ensure migrations are applied before or during setup.
- Establish a process for generating and applying new migrations as models evolve.

---

## 3. Clarify and Implement Seed Data Strategy

**Objective:** Standardize the loading of initial and sample data.

**Tasks:**
- **Decision Point:** Determine the definitive location for seed data:
    - **Option A:** Continue using `pyscrai/templates/` as the primary source for template seeding via `setup_database.py`.
    - **Option B:** Use the planned `pyscrai/databases/seeds/` directory for more comprehensive seed data (e.g., initial `EventType` definitions or other non-template master data).
- Based on the decision, refine `setup_database.py` or create a new seeding script (`pyscrai/databases/seeds/seed_data.py`) to:
    - Populate the `event_types` table with predefined system event types (e.g., `"agent_message"`, `"scenario_update"`, `"error_occurred"`).
    - Load any other necessary initial data.

---

## 4. Enhance Template Validation System

**Objective:** Ensure the integrity and correctness of agent and scenario templates beyond basic Pydantic schema validation.

**Tasks:**
- Review the structure of JSON fields within `AgentTemplate` (`personality_config`, `llm_config`, `tools_config`) and `ScenarioTemplate` (`config`, `agent_roles`, `event_flow`).
- Identify key-value pairs or structures within these JSON blobs that require specific validation rules (e.g., presence of certain keys, data types, valid enum values).
- Implement enhanced validation:
    - **Option A:** Embed more detailed Pydantic models or custom validators within existing schemas (`pyscrai/databases/models/schemas.py`).
    - **Option B:** Use JSON Schema definitions and a JSON schema validator to validate content during template creation and updates within the `TemplateManager`.
- Ensure validation errors provide clear, actionable feedback.

---

## 5. Complete CRUD Operations in TemplateManager

**Objective:** Provide full Create, Read, Update, and Delete (CRUD) functionality for agent and scenario templates as per Phase 1 deliverables.

**Tasks:**
- Review `pyscrai/factories/template_manager.py`.
- Implement the following methods if missing or incomplete:
    - `update_agent_template(template_id: int, update_data: AgentTemplateUpdate) -> AgentTemplateResponse`
    - `delete_agent_template(template_id: int) -> None`
    - `get_agent_template_by_id(template_id: int) -> Optional[AgentTemplateResponse]` (if different from by name)
    - `update_scenario_template(template_id: int, update_data: ScenarioTemplateUpdate) -> ScenarioTemplateResponse`
    - `delete_scenario_template(template_id: int) -> None`
    - `get_scenario_template_by_id(template_id: int) -> Optional[ScenarioTemplateResponse]` (if different from by name)
- Ensure these methods interact correctly with the database session and handle potential errors (e.g., template not found).
- Update corresponding Pydantic schemas in `schemas.py` for update operations if necessary.

---

## 6. Expand Database Testing

**Objective:** Ensure the reliability and correctness of all database components and operations.

**Tasks:**
- Expand test coverage in `pyscrai/tests/test_database.py`:
    - Add tests for all model relationships, including cascade behaviors.
    - Test all custom constraints.
- Expand test coverage in `pyscrai/tests/test_template_manager.py`:
    - Add tests for the newly implemented `update_` and `delete_` methods in `TemplateManager`.
    - Include tests for edge cases and error handling (e.g., updating/deleting non-existent templates).
    - Test the template validation logic (from step 4).
- Ensure tests use a dedicated test database or in-memory SQLite and properly manage setup and teardown of the database state for each test or test suite.

---

By systematically addressing these steps, the PyScrAI database foundation will be solidified, aligning with the project blueprint and paving the way for successful implementation of subsequent phases.
