# Getting Started with PyScrAI

This guide will help you get started with PyScrAI, from installation to running your first scenario.

## Prerequisites

- Python 3.12.7 or later
- UV for dependency management

## Installation

1. Clone the repository:
```powershell
git clone <repository-url>
cd PyScrAI
```

2. Create and activate a virtual environment:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate
```

3. Install dependencies:
```powershell
uv pip install -r requirements_phase1.txt
```

## Database Setup

1. Initialize the database:
```powershell
python setup_database.py --setup
```

This will:
- Create the SQLite database
- Apply migrations
- Load seed data (event types)
- Load sample templates

2. Verify the setup:
```powershell
python setup_database.py --list
```

## Basic Usage

Here's a simple example of creating and running a scenario:

```python
from pyscrai.factories import ScenarioFactory, AgentFactory
from pyscrai.engines import ActorEngine

# Create agents
agent_factory = AgentFactory()
narrator = agent_factory.create_agent_from_template("Narrator")
character = agent_factory.create_agent_from_template("Pope Leo XIII")

# Create scenario
scenario_factory = ScenarioFactory()
scenario = scenario_factory.create_scenario_from_template("Supernatural Vision Investigation")

# Run scenario
scenario.start()
```

## Next Steps

- Learn about [Templates](templates.md)
- Explore the [Engines](engines.md)
- Read the [API Reference](../api/README.md)
- Check out [Examples](../examples/README.md)
