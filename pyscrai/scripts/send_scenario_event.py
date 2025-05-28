#!/usr/bin/env python3
"""
PyScrAI Scenario Event Sender

This script provides a CLI interface for sending events to running scenarios.
It's a companion to the start_scenario.py script and allows interaction with
an already running scenario.

Usage:
    python -m pyscrai.scripts.send_scenario_event --id 123 --type "user_input" --message "Hello world"
"""
import asyncio
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import database connection
from pyscrai.databases.database import get_db_session

# Import framework components
from pyscrai.engines.scenario_runner import ScenarioRunner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("send_scenario_event")


async def send_event(
    scenario_run_id: int,
    event_type: str,
    event_data: Dict[str, Any],
    target_agent_id: Optional[int] = None,
    storage_path: str = "./data/scenario_storage"
) -> Dict[str, Any]:
    """
    Send an event to a running scenario.
    
    Args:
        scenario_run_id: ID of the target scenario run
        event_type: Type of event to send
        event_data: Event data payload
        target_agent_id: Optional specific agent to target
        storage_path: Path for scenario storage
        
    Returns:
        Dictionary containing the event response
    """
    logger.info(f"Sending '{event_type}' event to scenario {scenario_run_id}")
    
    # Create database session
    with get_db_session() as db:
        # Initialize the scenario runner with database session
        runner = ScenarioRunner(db, storage_base_path=storage_path)
        
        try:
            # Send the event to the scenario
            response = await runner.send_event_to_scenario(
                scenario_run_id=scenario_run_id,
                event_type=event_type,
                event_data=event_data,
                target_agent_id=target_agent_id
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to send event: {e}", exc_info=True)
            return {"error": str(e), "success": False}


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
    parser = argparse.ArgumentParser(description="Send an event to a running PyScrAI scenario")
    parser.add_argument("--id", required=True, type=int, help="ID of the scenario run")
    parser.add_argument("--type", required=True, help="Type of event to send")
    parser.add_argument("--message", help="Message content for the event")
    parser.add_argument("--data", help="Path to JSON file with event data")
    parser.add_argument("--agent", type=int, help="ID of the target agent (optional)")
    parser.add_argument("--storage", default="./data/scenario_storage", help="Path for scenario storage")
    
    args = parser.parse_args()
    
    # Prepare event data
    event_data = {}
    
    # Load data from file if provided
    if args.data:
        event_data = load_json_file(args.data)
        logger.info(f"Loaded event data from {args.data}")
    
    # Add message to event data if provided
    if args.message:
        event_data["prompt"] = args.message
        event_data["message"] = args.message
    
    # Send the event
    response = await send_event(
        scenario_run_id=args.id,
        event_type=args.type,
        event_data=event_data,
        target_agent_id=args.agent,
        storage_path=args.storage
    )
    
    # Output the response
    print(json.dumps(response, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
