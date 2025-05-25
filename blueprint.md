# PyScrAI Development Guide

## Project Overview

**PyScrAI** (System Scenario AI) represents a strategic pivot from the current ScrAI implementation toward a simplified, leverage-based approach using the Agno Agent Framework. Instead of maintaining extensive custom code for actor systems, cognitive cores, and scenario management, PyScrAI will create a thin orchestration layer that transforms Agno agents into specialized "engines" and "factories."

## Core Philosophy

### Principles
- **Minimize Custom Code**: Rely on Agno's proven OpenRouter/LMStudio integrations
- **Database-Driven**: Store scenarios, templates, and agent configurations
- **Agent-as-Engine**: Each Agno agent becomes a specialized processing unit
- **Factory Pattern**: Template-based rapid agent/scenario creation
- **Async-First**: Leverage Agno's async capabilities for concurrent simulations

### Benefits Over Current ScrAI
1. **Reduced Maintenance**: No custom LLM clients, cognitive cores, or actor systems
2. **Proven Reliability**: Agno's OpenRouter integration is battle-tested
3. **Rapid Prototyping**: Factory pattern enables quick scenario creation
4. **Scalability**: Async agents can handle multiple concurrent simulations
5. **Flexibility**: Database-driven configuration without code changes

## Architecture Overview

```
PyScrAI/pyscrai/
├── databases/              # SQLite/PostgreSQL for scenarios, templates, logs
│   ├── models/            # SQLAlchemy/Pydantic models
│   ├── migrations/        # Database schema migrations
│   └── seeds/             # Initial data and templates
├── engines/               # Agno agent wrappers for specific roles
│   ├── base_engine.py     # Abstract base for all engines
│   ├── actor_engine.py    # Character/persona simulation engine
│   ├── narrator_engine.py # Scenario narration and world-building
│   └── analyst_engine.py  # Result analysis and insights
├── factories/             # Template-based agent/scenario generators
│   ├── agent_factory.py   # Create agents from templates
│   ├── scenario_factory.py # Generate scenarios from templates
│   └── template_manager.py # Template CRUD operations
├── orchestrators/         # Lightweight coordination between agents
│   ├── scenario_runner.py # Multi-agent scenario execution
│   ├── event_manager.py   # Handle inter-agent events
│   └── state_tracker.py   # Monitor and log simulation state
├── templates/             # JSON/YAML scenario and agent templates
│   ├── agents/            # Agent behavior templates
│   ├── scenarios/         # Scenario configuration templates
│   └── events/            # Event type definitions
├── api/                   # FastAPI interface for management
│   ├── routes/            # API endpoints
│   ├── middleware/        # Auth, logging, validation
│   └── schemas/           # API request/response models
└── utils/                 # Shared utilities and helpers
    ├── config.py          # Configuration management
    ├── logging.py         # Centralized logging
    └── validation.py      # Data validation helpers
```

## Implementation Phases

### Phase 1: Foundation & Templates (Weeks 1-2)
**Objective**: Establish database foundation and template system

**Tasks**:
- Set up SQLite database with core schemas:
  - Agents (templates and instances)
  - Scenarios (configurations and runs)
  - Events (types and instances)
  - Logs (execution history)
- Create JSON/YAML template schemas for:
  - Agent personalities and behaviors
  - Scenario configurations
  - Event definitions
- Implement template factory classes
- Basic CRUD operations for templates

**Deliverables**:
- Database schema and migrations
- Template validation system
- Basic factory classes
- Sample templates (Pope Leo XIII scenario equivalent)

### Phase 2: Engine Implementation (Weeks 3-4)
**Objective**: Create Agno agent wrappers for specialized roles

**Tasks**:
- Implement base engine class with common Agno integration
- Create specialized engines:
  - **ActorEngine**: Character simulation with personality traits
  - **NarratorEngine**: World-building and scene description
  - **AnalystEngine**: Result analysis and pattern detection
- Event-driven communication between engines
- Result aggregation and structured output
- Error handling and fallback mechanisms

**Deliverables**:
- Working engine classes
- Inter-engine communication system
- Structured output schemas
- Error handling framework

### Phase 3: Orchestration & API (Weeks 5-6)
**Objective**: Multi-agent coordination and external interface

**Tasks**:
- Scenario runner for multi-agent simulations
- Real-time monitoring and intervention capabilities
- RESTful API for:
  - Template management
  - Scenario execution
  - Result retrieval
  - System monitoring
- Export/import capabilities for scenarios and results
- Basic web interface for scenario management

**Deliverables**:
- Complete orchestration system
- FastAPI-based management interface
- Import/export functionality
- Basic monitoring dashboard

## Technical Stack

### Core Dependencies
- **Python 3.12.10** (as per project requirements)
- **Agno Agent Framework** (OpenRouter/LMStudio integration)
- **FastAPI** (API framework)
- **SQLAlchemy** (Database ORM)
- **Pydantic** (Data validation and serialization)
- **AsyncIO** (Async operations)

### Database
- **SQLite** (development and small deployments)
- **PostgreSQL** (production and larger deployments)

### LLM Integration
- **OpenRouter** (via Agno's OpenRouterLLM class)
- **LMStudio** (via Agno's LMStudio integration)
- **Structured outputs** (Pydantic models for responses)

## Key Differences from Current ScrAI

| Current ScrAI | PyScrAI |
|---------------|---------|
| Custom actor system | Agno agent wrappers |
| Custom cognitive cores | Agno's built-in capabilities |
| Hardcoded scenarios | Database-driven templates |
| Complex inheritance | Simple composition |
| Custom LLM clients | Agno's proven integrations |
| Manual state management | Automatic via Agno/Pydantic |

## Getting Started

### Development Environment Setup

```powershell
# Activate virtual environment
C:\Users\tyler\dev\ScrAI\scrai\ScrAI\.venv\Scripts\Activate.ps1

# Install dependencies (will be added to pyproject.toml)
uv add agno-framework fastapi sqlalchemy pydantic-settings

# Initialize database
python -m PyScrAI.databases.init_db

# Run development server
python -m PyScrAI.api.main
```

### First Scenario Implementation

1. **Convert Pope Leo XIII prototype** to PyScrAI template
2. **Create agent templates** for Pope Leo XIII character
3. **Define scenario template** for supernatural vision
4. **Run scenario** through orchestrator
5. **Compare results** with current ScrAI implementation

## Migration Strategy

### From Current ScrAI
1. **Extract scenario data** from current implementations
2. **Convert to template format** (JSON/YAML)
3. **Map actor behaviors** to Agno agent configurations
4. **Validate results** match current system outputs
5. **Deprecate custom components** gradually

### Backward Compatibility
- **Export current scenarios** to new template format
- **Provide migration tools** for existing data
- **Maintain API compatibility** where possible

## Success Metrics

### Performance
- **Scenario execution time** < 50% of current ScrAI
- **Memory usage** < 30% of current ScrAI
- **Setup time** for new scenarios < 10 minutes

### Developer Experience
- **Lines of code** reduced by 70%
- **Time to implement** new scenario < 2 hours
- **Bug reports** reduced by 60%

### Reliability
- **LLM integration errors** < 1% (vs current rates)
- **System uptime** > 99.5%
- **Successful scenario completion** > 95%

## Future Enhancements

### Advanced Features
- **Multi-model orchestration** (different LLMs for different roles)
- **Real-time collaboration** (multiple users in same scenario)
- **Advanced analytics** (pattern recognition, behavior analysis)
- **Plugin system** (custom engines and factories)

### Integration Possibilities
- **Discord bots** for interactive scenarios
- **Web interface** for non-technical users
- **API integrations** with external systems
- **Cloud deployment** options

## Conclusion

PyScrAI represents a fundamental shift toward sustainable, maintainable AI scenario simulation. By leveraging the Agno Agent Framework's mature capabilities, we can achieve better results with significantly less code, faster development cycles, and improved reliability.

The key insight is that complexity should be handled by proven frameworks, while our code focuses on orchestration, configuration, and domain-specific logic. This approach positions PyScrAI for long-term success and rapid iteration.

---

**Project Status**: Planning Phase  
**Next Milestone**: Phase 1 Foundation & Templates  
**Estimated Completion**: 6 weeks from start  
**Team Requirements**: 1-2 developers familiar with Python async programming