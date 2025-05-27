## Understanding Your Database Setup

Your `database.py` script configures a SQLite database at `PROJECT_ROOT/data/pyscrai.db` using SQLAlchemy as the ORM. The `base.py` file provides the `Base` class for your declarative models. Core models like `AgentTemplate` and `ScenarioTemplate` are defined in `core_models.py` and will store your template data. Additional models (e.g., for events, logs, etc.) are expected in the `pyscrai/databases/models/` directory and should inherit from the same `Base`.

---

## Initializing the Database (Creating Tables & Seeding Data)

The `database.py` script includes an `init_database()` function, which:

1. **Creates Tables:**  
    Calls `Base.metadata.create_all(bind=engine)` to create all tables defined by your SQLAlchemy models.

2. **Seeds Initial Data:**  
    Invokes `_seed_initial_data()`, which currently seeds `EventType` data if the table is empty.

**To initialize the database, run:**

```bash
python -m pyscrai.databases.database
```
*(Adjust the path as needed for your project structure.)*

When run directly, this script calls `init_database()` and prints database information, including table counts.

---

## Verifying Database Creation

After running the script:

- A `pyscrai.db` file should appear in the `data` subdirectory (e.g., `PyScrAI/data/pyscrai.db`).
- The console output will display table counts, confirming table creation and event type seeding.

---

## Seeding Agent & Scenario Templates

Currently, `_seed_initial_data()` only seeds `EventType` models. To load your agent and scenario templates (from JSON files in `pyscrai/templates/`) into the `AgentTemplate` and `ScenarioTemplate` tables:

**Recommendation:**  
Expand `_seed_initial_data()` in `database.py` to read your JSON template files and create `AgentTemplate` and `ScenarioTemplate` objects, adding them to the database session.

**Alternatively:**  
Use the `pyscrai/databases/seeds/seed_data.py` script for this purpose. In `seed_data.py`:

- Import your `AgentTemplate`, `ScenarioTemplate` models, and the session (`SessionLocal` or `get_db_session`) from `database.py`.
- Read the JSON files.
- Create model instances from the JSON data.
- Add them to a database session and commit.

Run this seeding script after `init_database()` has created the tables.

---

## Using the Database in Your Application

- `database.py` provides a `get_db()` function for obtaining a database session (useful as a dependency in frameworks like FastAPI).
- It also provides `get_db_session()` for direct session usage elsewhere.
- **Remember:** Always close sessions when done.





Here's what we've accomplished:

✅ Fixed import errors - Resolved all the missing imports for QueuedEvent, SystemMetrics, and TemplateUsage
✅ Fixed SQLAlchemy relationship errors - Corrected the foreign key definitions and relationships between models
✅ Database creation - All 8 tables were created successfully
✅ Initial data seeding - Successfully seeded 3 basic event types
The database is now properly initialized with:

Path: pyscrai.db
Tables created: 8 tables (agent_templates, scenario_templates, agent_instances, scenario_runs, event_types, event_instances, execution_logs, engine_states)
Initial data: 3 event types seeded
Key fixes that were made:

Import fixes: Added missing imports for QueuedEvent, SystemMetrics, and TemplateUsage to the models __init__.py
Foreign key fixes: Changed ForeignKey definitions from module paths to table names (e.g., "agent_instances.id" instead of f"{CORE_MODELS_PATH}.AgentInstance.id")
Relationship fixes:
Removed the incorrect AgentTemplate.scenario_runs relationship
Added the missing EventInstance.queued_events relationship
Datetime fixes: Updated all datetime references to use datetime.datetime.utcnow
The PyScrAI database is now ready for use! You can run scenarios, create agent instances, log events, and track execution through the properly configured SQLAlchemy ORM models.