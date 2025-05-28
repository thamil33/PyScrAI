#!/usr/bin/env python3
"""
PyScrAI Scenario Integration Test Script

This script tests the integration of the ScenarioFactory, database, and ScenarioRunner
to ensure the scenario execution pipeline works end-to-end.

Usage:
    python -m pyscrai.scripts.test_scenario_integration
"""
import asyncio
import logging
import sys
from pyscrai.databases.database import get_db_session
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

logger = logging.getLogger("test_scenario_integration")


async def test_integration(template_name: str = "demo_conversation"):
    """
    Test the integration between ScenarioFactory, database and ScenarioRunner.
    
    Args:
        template_name: Name of the template to use for testing
    """
    logger.info("Starting scenario integration test")
    
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
            
            # Step 2: Test ScenarioRunner initialization with factory
            logger.info("Initializing ScenarioRunner with database connection")
            runner = ScenarioRunner(db)
            
            # Step 3: Test agent creation and start process
            logger.info(f"Starting scenario {scenario_run.id}")
            scenario_run_id = await runner.start_scenario(template_name)
            logger.info(f"Scenario started with run ID {scenario_run_id}")
            
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
            
            return True
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}", exc_info=True)
            return False


async def main():
    """Main function for running the integration test."""
    success = await test_integration()
    
    if success:
        logger.info("Integration test completed successfully!")
        logger.info("ScenarioRunner is correctly integrated with ScenarioFactory and database")
    else:
        logger.error("Integration test failed. Please check the logs for details.")


if __name__ == "__main__":
    asyncio.run(main())
