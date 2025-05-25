# Database Architecture in PyScrAI

This guide explains the database architecture of PyScrAI.

## Overview

PyScrAI uses SQLite with SQLAlchemy ORM for its database operations, with Alembic handling schema migrations.

## Database Schema

### Core Tables

1. **Agent Templates** (`agent_templates`)
   - Template definitions for AI characters
   ```sql
   CREATE TABLE agent_templates (
       id INTEGER PRIMARY KEY,
       name VARCHAR(100) UNIQUE NOT NULL,
       description TEXT,
       personality_config JSON,
       llm_config JSON,
       tools_config JSON,
       created_at DATETIME,
       updated_at DATETIME
   )
   ```

2. **Scenario Templates** (`scenario_templates`)
   - Template definitions for scenarios
   ```sql
   CREATE TABLE scenario_templates (
       id INTEGER PRIMARY KEY,
       name VARCHAR(100) UNIQUE NOT NULL,
       description TEXT,
       config JSON,
       agent_roles JSON,
       event_flow JSON,
       created_at DATETIME,
       updated_at DATETIME
   )
   ```

3. **Event Types** (`event_types`)
   - Definitions of supported event types
   ```sql
   CREATE TABLE event_types (
       id INTEGER PRIMARY KEY,
       name VARCHAR(100) UNIQUE NOT NULL,
       description TEXT,
       schema JSON,
       created_at DATETIME
   )
   ```

### Runtime Tables

4. **Scenario Runs** (`scenario_runs`)
   - Active or completed scenario instances
   ```sql
   CREATE TABLE scenario_runs (
       id INTEGER PRIMARY KEY,
       template_id INTEGER,
       name VARCHAR(100),
       status VARCHAR(20),
       config JSON,
       results JSON,
       started_at DATETIME,
       completed_at DATETIME,
       created_at DATETIME,
       FOREIGN KEY(template_id) REFERENCES scenario_templates(id)
   )
   ```

5. **Agent Instances** (`agent_instances`)
   - Active agent instances in scenarios
   ```sql
   CREATE TABLE agent_instances (
       id INTEGER PRIMARY KEY,
       template_id INTEGER,
       scenario_run_id INTEGER,
       instance_name VARCHAR(100),
       runtime_config JSON,
       state JSON,
       created_at DATETIME,
       FOREIGN KEY(template_id) REFERENCES agent_templates(id),
       FOREIGN KEY(scenario_run_id) REFERENCES scenario_runs(id)
   )
   ```

6. **Event Instances** (`event_instances`)
   - Events that occur during scenario runs
   ```sql
   CREATE TABLE event_instances (
       id INTEGER PRIMARY KEY,
       scenario_run_id INTEGER,
       event_type_id INTEGER,
       source_agent_id INTEGER,
       target_agent_id INTEGER,
       data JSON,
       processed BOOLEAN,
       created_at DATETIME,
       FOREIGN KEY(scenario_run_id) REFERENCES scenario_runs(id),
       FOREIGN KEY(event_type_id) REFERENCES event_types(id),
       FOREIGN KEY(source_agent_id) REFERENCES agent_instances(id),
       FOREIGN KEY(target_agent_id) REFERENCES agent_instances(id)
   )
   ```

7. **Execution Logs** (`execution_logs`)
   - Detailed execution logs for debugging
   ```sql
   CREATE TABLE execution_logs (
       id INTEGER PRIMARY KEY,
       scenario_run_id INTEGER,
       agent_instance_id INTEGER,
       level VARCHAR(10),
       message TEXT,
       data JSON,
       created_at DATETIME,
       FOREIGN KEY(scenario_run_id) REFERENCES scenario_runs(id),
       FOREIGN KEY(agent_instance_id) REFERENCES agent_instances(id)
   )
   ```

## Data Management

### Migrations

Migrations are handled by Alembic:
```bash
# View migration status
alembic current

# Create new migration
alembic revision -m "description"

# Apply migrations
alembic upgrade head
```

### Seed Data

PyScrAI uses a hybrid approach for seed data:

1. **System Data** (`pyscrai/databases/seeds/`)
   - Core event types
   - System configurations

2. **Templates** (`pyscrai/templates/`)
   - Agent templates
   - Scenario templates
   - Event templates

## Using the Database

### Basic Operations

```python
from pyscrai.databases import get_db_session
from pyscrai.databases.models import AgentTemplate

# Get a database session
db = get_db_session()

try:
    # Query templates
    templates = db.query(AgentTemplate).all()
    
    # Create new template
    new_template = AgentTemplate(
        name="Example",
        description="An example template"
    )
    db.add(new_template)
    db.commit()
finally:
    db.close()
```

### Using the Template Manager

```python
from pyscrai.factories.template_manager import TemplateManager

manager = TemplateManager(db)
templates = manager.list_agent_templates()
```

## Best Practices

1. **Session Management**
   - Always use context managers or try/finally blocks
   - Close sessions after use
   - Use `get_db_session()` for manual sessions

2. **Migrations**
   - Always create migrations for schema changes
   - Test migrations both up and down
   - Include data migrations when needed

3. **Data Integrity**
   - Use foreign key constraints
   - Include appropriate indexes
   - Validate data before insertion

4. **Error Handling**
   - Catch and log database errors
   - Implement proper rollback logic
   - Validate input data
