#!/usr/bin/env python3
"""
PyScrAI Scenario Integration Script

This script tests the integration of the ScenarioFactory, database, and ScenarioRunner
to ensure the scenario execution pipeline works end-to-end.

Usage:
    python -m pyscrai.scripts.test_scenario_integration
"""
import asyncio
import logging
import sys
import json
import time
from typing import Dict, Any, List, Optional
from pyscrai.databases.database import get_db_session
from pyscrai.factories.scenario_factory import ScenarioFactory
from pyscrai.engines.scenario_runner import ScenarioRunner
from pyscrai.databases.models import ScenarioTemplate, AgentTemplate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("test_scenario_integration")


async def test_integration(template_name: str = "demo_conversation", event_sequence: Optional[List[Dict[str, Any]]] = None):
    """
    Test the integration between ScenarioFactory, database and ScenarioRunner.
    
    Args:
        template_name: Name of the template to use for testing
        event_sequence: Optional sequence of events to run in the scenario
    """
    logger.info("Starting scenario integration test")
    
    if event_sequence is None:
        # Default event sequence for testing
        event_sequence = [
            {
                "event_type": "user_prompt",
                "data": {
                    "prompt": "Let's start a conversation about AI ethics.",
                    "priority": 10
                }
            },
            {
                "event_type": "scene_transition",
                "data": {
                    "scene_name": "discussion",
                    "description": "A thoughtful discussion about the future of AI"
                },
                "delay_seconds": 2
            }
        ]
    
    with get_db_session() as db:
        try:
            # Step 1: Test ScenarioFactory
            logger.info(f"Creating scenario run from template '{template_name}'")
            factory = ScenarioFactory(db)
            scenario_run = factory.create_scenario_run_from_template(
                template_name=template_name,
                run_name=f"integration_test_{template_name}"
            )
            
            logger.info(f"Created scenario run with ID {scenario_run.id}")
            
            # List available templates
            templates = db.query(ScenarioTemplate).all()
            logger.info(f"Available scenario templates: {[t.name for t in templates]}")
            
            # List available agent templates
            agent_templates = db.query(AgentTemplate).all()
            logger.info(f"Available agent templates: {[t.name for t in agent_templates]}")
            
            # Step 2: Test ScenarioRunner initialization with factory
            logger.info("Initializing ScenarioRunner with database connection")
            runner = ScenarioRunner(db)
            
            # Step 3: Test agent creation and start process
            logger.info(f"Starting scenario {scenario_run.id}")
            scenario_run_id = await runner.start_scenario(template_name)
            logger.info(f"Scenario started with run ID {scenario_run_id}")
            
            # Wait a moment for initialization
            await asyncio.sleep(1)
            
            # Run the event sequence
            logger.info(f"Running event sequence with {len(event_sequence)} events")
            results = await runner.run_scenario_sequence(
                scenario_run_id, event_sequence
            )
            
            # Monitor the scenario for a while
            logger.info("Monitoring scenario status...")
            for _ in range(5):
                status = await runner.monitor_scenario(scenario_run_id)
                logger.info(f"Current status: {json.dumps(status, default=str, indent=2)}")
                await asyncio.sleep(2)
            
            # Step 4: Verify database integration by checking status
            status = runner.get_scenario_status(scenario_run_id)
            logger.info(f"Scenario status: {status}")
            
            # Step 5: Test state persistence
            await runner.save_state_snapshot(scenario_run_id)
            logger.info("State snapshot saved to database")
            
            # Step 6: Test stopping the scenario
            await runner.stop_scenario(scenario_run_id)
            logger.info(f"Scenario {scenario_run_id} stopped")
            
            # Step 7: Verify scenario data in database
            scenario_data = await runner.load_scenario_from_db(scenario_run_id)
            logger.info(f"Loaded scenario data from database: {scenario_data['scenario_run'].status}")
            
            logger.info(f"Scenario {scenario_run_id} completed successfully")
            logger.info("Framework integration is working correctly")
            
            return scenario_run_id, results
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}", exc_info=True)
            return None, None


async def main():
    """Main function for running the integration test."""
    if len(sys.argv) > 1:
        template_name = sys.argv[1]
    else:
        template_name = "demo_conversation"
    
    scenario_id, results = await test_integration(template_name)
    
    if scenario_id:
        logger.info(f"Scenario run {scenario_id} completed")
        if results:
            logger.info(f"Event results: {json.dumps(results, default=str, indent=2)}")
    else:
        logger.error("Scenario run failed. Please check the logs for details.")
    
    logger.info("Scenario integration script completed")


if __name__ == "__main__":
    asyncio.run(main())
