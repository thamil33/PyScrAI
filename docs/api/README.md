# PyScrAI API Reference

This section provides detailed documentation for PyScrAI's API.

## Package Structure

- [pyscrai](#pyscrai)
  - [databases](#databases)
  - [engines](#engines)
  - [factories](#factories)
  - [templates](#templates)
  - [utils](#utils)

## Modules

### pyscrai

The root package containing core functionality.

### databases

Database models and management:

- [Base Models](models/base.md)
- [Agent Models](models/agent_models.md)
- [Scenario Models](models/scenario_models.md)
- [Event Models](models/event_models.md)
- [Log Models](models/log_models.md)

### engines

Simulation engines:

- [BaseEngine](engines/base_engine.md)
- [ActorEngine](engines/actor_engine.md)

### factories

Factory classes and managers:

- [AgentFactory](factories/agent_factory.md)
- [ScenarioFactory](factories/scenario_factory.md)
- [TemplateManager](factories/template_manager.md)

### templates

Template definitions and schemas:

- [Agent Templates](templates/agent_templates.md)
- [Scenario Templates](templates/scenario_templates.md)
- [Event Templates](templates/event_templates.md)

### utils

Utility functions and configuration:

- [Config](utils/config.md)

## Type Definitions

Common types and interfaces used throughout PyScrAI:

- [Type Definitions](types.md)
