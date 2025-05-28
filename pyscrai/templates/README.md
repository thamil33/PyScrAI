# PyScrAI Templates

This directory contains all the templates used by PyScrAI, organized by type.

## Directory Structure

- `/agents`: Agent templates that define behavior, personality, tools, and LLM configurations
- `/scenarios`: Scenario templates that define event flows, agent roles, and interaction rules
- `/events`: Event type definitions that specify the structure of events in the system

## Automatic Template Loading

Templates in these directories are automatically loaded into the database during initialization.
This happens when:

1. The database is first created
2. The database is reset
3. The `init_database()` function is called

## Template Management

You can manage templates using the template manager script:

```bash
# List all templates in the database
python -m pyscrai.scripts.template_manager list

# Verify templates in a directory
python -m pyscrai.scripts.template_manager verify-dir pyscrai/templates/agents

# Verify a specific template file
python -m pyscrai.scripts.template_manager verify pyscrai/templates/agents/my_template.json

# Export a template from database to file
python -m pyscrai.scripts.template_manager export agent 1 output_dir

# Export all templates to their respective directories
python -m pyscrai.scripts.template_manager export-all
```

## Template Format

Templates must adhere to the validators defined in `pyscrai/databases/models/template_validators.py`.

### Agent Templates

Agent templates require fields like:
- `name`: Unique name for the template
- `engine_type`: Engine to use ("narrator", "actor", "analyst")
- `personality_config`: Agent's personality traits
- `llm_config`: LLM settings like model, temperature, etc.
- And other configurations as defined in `AgentTemplateValidator`

### Scenario Templates

Scenario templates require fields like:
- `name`: Unique name for the template
- `config`: General configuration including max turns, timeout, etc.
- `agent_roles`: Mapping of role names to agent template specifications
- `event_flow`: Definition of events and their conditions
- And other configurations as defined in `ScenarioTemplateValidator`

## Creating New Templates

To create a new template:

1. Create a JSON file in the appropriate directory
2. Populate it with required fields according to the validator
3. Verify the template using the `verify` command
4. Run the database initialization script to load it into the database

For more details, refer to the template validator definitions in the code.
