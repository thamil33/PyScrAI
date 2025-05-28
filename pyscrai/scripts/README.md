# PyScrAI Scripts

This directory contains utility scripts for working with PyScrAI scenarios.

## Available Scripts

### 1. `start_scenario.py`
Starts a new scenario from a template. This initializes all required components and prepares the framework to begin scenario execution.

```bash
python -m pyscrai.scripts.start_scenario --template "template_name" --config config.json --agents agents.json
```

**Arguments:**
- `--template`: (Required) Name of the scenario template to use
- `--config`: (Optional) Path to a JSON file with scenario configuration
- `--agents`: (Optional) Path to a JSON file with agent configurations
- `--storage`: (Optional) Path for scenario storage (default: "./data/scenario_storage")

### 2. `send_scenario_event.py`
Sends events to a running scenario. This allows interaction with an already running scenario.

```bash
python -m pyscrai.scripts.send_scenario_event --id 123 --type "user_input" --message "Hello world"
```

**Arguments:**
- `--id`: (Required) ID of the scenario run
- `--type`: (Required) Type of event to send
- `--message`: (Optional) Message content for the event
- `--data`: (Optional) Path to JSON file with event data
- `--agent`: (Optional) ID of the target agent
- `--storage`: (Optional) Path for scenario storage (default: "./data/scenario_storage")

### 3. `monitor_scenario.py`
Monitors the status of running scenarios.

```bash
# Monitor a single scenario
python -m pyscrai.scripts.monitor_scenario --id 123

# List all scenarios
python -m pyscrai.scripts.monitor_scenario --list

# Watch scenario updates in real-time
python -m pyscrai.scripts.monitor_scenario --id 123 --watch
```

**Arguments:**
- `--id`: ID of the scenario run to monitor
- `--list`: List all scenarios
- `--status`: Filter scenarios by status (with --list)
- `--limit`: Maximum number of scenarios to list (default: 20)
- `--storage`: Path for scenario storage (default: "./data/scenario_storage")
- `--watch`: Watch scenario status in real-time
- `--interval`: Update interval in seconds for watch mode (default: 5)

### 4. `scenario_integration.py`
Tests the integration between ScenarioFactory, database, and ScenarioRunner.

```bash
python -m pyscrai.scripts.scenario_integration
```

This script runs a complete end-to-end test of the framework components to ensure everything is working together correctly.

## Example Workflow

1. Start a new scenario:
```bash
python -m pyscrai.scripts.start_scenario --template "demo_conversation"
```

2. Send an event to the scenario (using the ID returned from step 1):
```bash
python -m pyscrai.scripts.send_scenario_event --id 123 --type "user_input" --message "Tell me a story about AI"
```

3. Monitor the scenario:
```bash
python -m pyscrai.scripts.monitor_scenario --id 123 --watch
```
