#!/usr/bin/env python3
"""
PyScrAI Scenario Monitor Script

This script provides a CLI interface for monitoring running scenarios.
It allows checking the status, state, and agent activities for active scenarios.

Usage:
    python -m pyscrai.scripts.monitor_scenario --id 123
    python -m pyscrai.scripts.monitor_scenario --list
"""
import asyncio
import argparse
import json
import logging
import sys
from typing import Dict, Any, Optional, List

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

logger = logging.getLogger("monitor_scenario")


async def get_scenario_status(
    scenario_run_id: int,
    storage_path: str = "./data/scenario_storage"
) -> Dict[str, Any]:
    """
    Get the status and state of a running scenario.
    
    Args:
        scenario_run_id: ID of the scenario run to monitor
        storage_path: Path for scenario storage
        
    Returns:
        Dictionary containing scenario status
    """
    logger.info(f"Retrieving status for scenario {scenario_run_id}")
    
    # Create database session
    with get_db_session() as db:
        # Initialize the scenario runner with database session
        runner = ScenarioRunner(db, storage_base_path=storage_path)
        
        try:
            # Get scenario status
            return await runner.monitor_scenario(scenario_run_id)
            
        except Exception as e:
            logger.error(f"Failed to get scenario status: {e}", exc_info=True)
            return {"error": str(e), "success": False}


async def list_scenarios(
    status_filter: Optional[str] = None,
    storage_path: str = "./data/scenario_storage",
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    List all scenarios matching the filter.
    
    Args:
        status_filter: Optional status to filter by
        storage_path: Path for scenario storage
        limit: Maximum number of scenarios to return
        
    Returns:
        List of scenario data dictionaries
    """
    logger.info(f"Listing scenarios{f' with status {status_filter}' if status_filter else ''}")
    
    # Create database session
    with get_db_session() as db:
        # Initialize the scenario runner with database session
        runner = ScenarioRunner(db, storage_base_path=storage_path)
        
        try:
            # List scenarios
            return runner.list_scenarios(status_filter, limit)
            
        except Exception as e:
            logger.error(f"Failed to list scenarios: {e}", exc_info=True)
            return [{"error": str(e), "success": False}]


async def main():
    """Entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Monitor PyScrAI scenarios")
    parser.add_argument("--id", type=int, help="ID of the scenario run to monitor")
    parser.add_argument("--list", action="store_true", help="List all scenarios")
    parser.add_argument("--status", help="Filter scenarios by status (with --list)")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of scenarios to list")
    parser.add_argument("--storage", default="./data/scenario_storage", help="Path for scenario storage")
    parser.add_argument("--watch", action="store_true", help="Watch scenario status in real-time")
    parser.add_argument("--interval", type=int, default=5, help="Update interval in seconds (with --watch)")
    
    args = parser.parse_args()
    
    # Check if we should list all scenarios
    if args.list:
        scenarios = await list_scenarios(args.status, args.storage, args.limit)
        print(json.dumps(scenarios, indent=2))
        return
    
    # Check if we should monitor a specific scenario
    if args.id:
        # If watch mode is enabled, continuously update
        if args.watch:
            try:
                while True:
                    status = await get_scenario_status(args.id, args.storage)
                    # Clear terminal (works on most terminals)
                    print("\033c", end="")
                    print(f"Scenario {args.id} Status (updated every {args.interval} seconds)")
                    print("=" * 80)
                    print(json.dumps(status, indent=2))
                    print("\nPress Ctrl+C to exit.")
                    await asyncio.sleep(args.interval)
            except KeyboardInterrupt:
                logger.info("Monitoring stopped")
        else:
            # Single status check
            status = await get_scenario_status(args.id, args.storage)
            print(json.dumps(status, indent=2))
        return
    
    # If no action specified, show help
    parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
