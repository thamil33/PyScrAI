#!/usr/bin/env python3
"""
PyScrAI Scenario Starter Script

This script provides a simple CLI interface for starting scenarios from templates.
It handles the instantiation of agents, connection to engine components,
and prepares the framework to begin scenario execution.

Usage:
    python -m pyscrai.scripts.start_scenario --template "BasicAdventure"
"""
import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import database connection
from pyscrai.databases.database import get_db_session

# Import framework components
from pyscrai.factories.scenario_factory import ScenarioFactory
from pyscrai.engines.scenario_runner import ScenarioRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("start_scenario")


async def start_scenario(
    template_name: str,
    scenario_config: Optional[Dict[str, Any]] = None,
    agent_configs: Optional[List[Dict[str, Any]]] = None,
    storage_path: str = "./data/scenario_storage"
) -> int:
    """
    Start a scenario from a template with the given configuration.
    
    Args:
        template_name: Name of the scenario template to use
        scenario_config: Optional configuration for the scenario
        agent_configs: Optional configurations for the agents
        storage_path: Path for storing scenario data
        
    Returns:
        The scenario run ID if successful
    """
    logger.info(f"Starting scenario from template '{template_name}'")
    
    # Create database session
    with get_db_session() as db:
        # Initialize the scenario runner with database session
        runner = ScenarioRunner(db, storage_base_path=storage_path)
        
        try:
            # Start the scenario using the runner
            scenario_run_id = await runner.start_scenario(
                template_name=template_name,
                scenario_config=scenario_config,
                agent_configs=agent_configs
            )
            
            logger.info(f"Scenario started successfully with run ID: {scenario_run_id}")
            logger.info("The scenario is now running and ready for events/interaction")
            
            # Return the run ID for further interaction
            return scenario_run_id
            
        except Exception as e:
            logger.error(f"Failed to start scenario: {e}", exc_info=True)
            raise
        

def load_json_file(file_path: str) -> Dict[str, Any]:
    """
    Load a JSON file into a dictionary.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Dictionary with the loaded JSON data
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(path, 'r') as f:
        return json.load(f)


async def main():
    """Entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Start a PyScrAI scenario from a template")
    parser.add_argument("--template", required=True, help="Name of the scenario template")
    parser.add_argument("--config", help="Path to scenario configuration JSON file")
    parser.add_argument("--agents", help="Path to agent configurations JSON file")
    parser.add_argument("--storage", default="./data/scenario_storage", help="Path for scenario storage")
    
    args = parser.parse_args()
    
    # Load configuration files if provided
    scenario_config = None
    if args.config:
        scenario_config = load_json_file(args.config)
        logger.info(f"Loaded scenario configuration from {args.config}")
    
    agent_configs = None
    if args.agents:
        agent_configs = load_json_file(args.agents)
        logger.info(f"Loaded agent configurations from {args.agents}")
    
    # Start the scenario
    scenario_run_id = await start_scenario(
        template_name=args.template,
        scenario_config=scenario_config,
        agent_configs=agent_configs,
        storage_path=args.storage
    )
    
    logger.info(f"Scenario {scenario_run_id} is running.")
    logger.info("Press Ctrl+C to exit (scenario will continue running in background).")
    
    # Keep the script running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Script terminated by user. Scenario continues running.")


if __name__ == "__main__":
    asyncio.run(main())
