"""
Scenario Runner for PyScrAI.

This module implements the scenario execution system that connects scenarios,
agents, and engines through the orchestration system. This is the main entry
point for running complete scenarios with real LLM interactions.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from ..databases.models import ScenarioRun, ScenarioTemplate, AgentInstance
from ..factories.scenario_factory import ScenarioFactory
from .orchestration.engine_manager import EngineManager

logger = logging.getLogger(__name__)


class ScenarioRunner:
    """
    Main scenario execution engine that orchestrates the complete scenario lifecycle.
    Integrates scenarios, agents, engines, and the orchestration system.
    """
    
    def __init__(self, db: Session, storage_base_path: str = "./data/scenario_storage"):
        """
        Initialize the Scenario Runner.
        
        Args:
            db: Database session for scenario operations
            storage_base_path: Base path for scenario storage files
        """
        self.db = db
        self.storage_base_path = storage_base_path
        
        # Initialize core components
        self.scenario_factory = ScenarioFactory(db)
        self.engine_manager = EngineManager(db, storage_base_path)
        
        # Track active scenario runs
        self.active_scenarios: Dict[int, Dict[str, Any]] = {}
        
        logger.info("ScenarioRunner initialized")
    
    async def start_scenario(
        self, 
        template_name: str,
        scenario_config: Optional[Dict[str, Any]] = None,
        agent_configs: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[int]:
        """
        Start a new scenario execution.
        
        Args:
            template_name: Name of the scenario template to use
            scenario_config: Optional configuration overrides for the scenario
            agent_configs: Optional list of agent configurations
            
        Returns:
            Scenario run ID if successful, None if failed
        """
        try:
            logger.info(f"Starting scenario from template: {template_name}")
            
            # Create scenario run from template
            scenario_run = self.scenario_factory.create_scenario_run_from_template(
                template_name=template_name,
                config_overrides=scenario_config or {}
            )
            
            if not scenario_run:
                logger.error(f"Failed to create scenario run from template: {template_name}")
                return None
            
            scenario_run_id = scenario_run.id
            logger.info(f"Created scenario run {scenario_run_id}")
            
            # Create agents if configurations provided
            if agent_configs:
                for agent_config in agent_configs:
                    agent_instance = self.scenario_factory.create_agent_instance(
                        scenario_run_id=scenario_run_id,
                        template_name=agent_config.get("template_name"),
                        instance_name=agent_config.get("instance_name"),
                        runtime_config=agent_config.get("runtime_config", {})
                    )
                    if agent_instance:
                        logger.info(f"Created agent instance {agent_instance.id} for scenario {scenario_run_id}")
            
            # Start the scenario execution through EngineManager
            agent_results = await self.engine_manager.start_scenario_execution(
                scenario_run_id, 
                scenario_run.configuration or {}
            )
            
            # Track the active scenario
            self.active_scenarios[scenario_run_id] = {
                "scenario_run": scenario_run,
                "started_at": asyncio.get_event_loop().time(),
                "agent_results": agent_results,
                "status": "running"
            }
            
            # Subscribe to scenario events
            self._setup_scenario_event_handlers(scenario_run_id)
            
            logger.info(f"Scenario {scenario_run_id} started successfully with {len(agent_results)} agents")
            return scenario_run_id
            
        except Exception as e:
            logger.error(f"Failed to start scenario {template_name}: {e}", exc_info=True)
            return None
    
    async def stop_scenario(self, scenario_run_id: int) -> bool:
        """
        Stop a running scenario.
        
        Args:
            scenario_run_id: ID of the scenario run to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        try:
            if scenario_run_id not in self.active_scenarios:
                logger.warning(f"Scenario {scenario_run_id} is not active")
                return False
            
            logger.info(f"Stopping scenario {scenario_run_id}")
            
            # Stop through EngineManager
            agent_results = await self.engine_manager.stop_scenario_execution(scenario_run_id)
            
            # Update scenario status
            scenario_info = self.active_scenarios[scenario_run_id]
            scenario_info["status"] = "stopped"
            scenario_info["stopped_at"] = asyncio.get_event_loop().time()
            scenario_info["stop_results"] = agent_results
            
            # Update database
            scenario_run = scenario_info["scenario_run"]
            self.scenario_factory.update_scenario_run_status(scenario_run_id, "completed")
            
            # Remove from active scenarios
            del self.active_scenarios[scenario_run_id]
            
            logger.info(f"Scenario {scenario_run_id} stopped successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop scenario {scenario_run_id}: {e}", exc_info=True)
            return False
    
    async def send_event_to_scenario(
        self,
        scenario_run_id: int,
        event_type: str,
        event_data: Dict[str, Any],
        target_agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send an event to a running scenario.
        
        Args:
            scenario_run_id: ID of the target scenario
            event_type: Type of event to send
            event_data: Event payload data
            target_agent_id: Optional specific agent to target
            
        Returns:
            Dictionary containing event results
        """
        try:
            if scenario_run_id not in self.active_scenarios:
                return {"error": f"Scenario {scenario_run_id} is not active"}
            
            logger.info(f"Sending {event_type} event to scenario {scenario_run_id}")
            
            # Create event payload
            event_payload = {
                "event_type": event_type,
                "scenario_run_id": scenario_run_id,
                "timestamp": asyncio.get_event_loop().time(),
                **event_data
            }
            
            # Send to specific agent or broadcast to all
            if target_agent_id:
                response = await self.engine_manager.send_message_to_agent(
                    target_agent_id,
                    event_payload.get("prompt", ""),
                    event_payload
                )
                results = {target_agent_id: response}
            else:
                results = await self.engine_manager.broadcast_to_scenario_agents(
                    scenario_run_id,
                    event_payload.get("prompt", ""),
                    event_payload
                )
            
            # Publish event through event bus
            self.engine_manager.event_bus.publish(f"scenario.event.{event_type}", {
                "scenario_run_id": scenario_run_id,
                "event_payload": event_payload,
                "results": results
            })
            
            return {
                "event_type": event_type,
                "scenario_run_id": scenario_run_id,
                "results": results,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Failed to send event to scenario {scenario_run_id}: {e}", exc_info=True)
            return {"error": str(e), "success": False}
    
    def get_scenario_status(self, scenario_run_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a scenario.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            Dictionary containing scenario status or None if not found
        """
        if scenario_run_id not in self.active_scenarios:
            return None
        
        # Get status from EngineManager
        engine_status = self.engine_manager.get_scenario_status(scenario_run_id)
        
        # Combine with local tracking info
        local_info = self.active_scenarios[scenario_run_id]
        
        return {
            **engine_status,
            "local_status": local_info["status"],
            "started_at": local_info["started_at"],
            "runtime_seconds": asyncio.get_event_loop().time() - local_info["started_at"]
        }
    
    def list_active_scenarios(self) -> List[Dict[str, Any]]:
        """
        Get a list of all active scenarios.
        
        Returns:
            List of scenario status dictionaries
        """
        active_list = []
        for scenario_id in self.active_scenarios:
            status = self.get_scenario_status(scenario_id)
            if status:
                active_list.append(status)
        
        return active_list
    
    def _setup_scenario_event_handlers(self, scenario_run_id: int):
        """
        Set up event handlers for a scenario.
        
        Args:
            scenario_run_id: ID of the scenario run
        """
        event_bus = self.engine_manager.event_bus
        
        # Handler for agent responses
        def handle_agent_response(data):
            logger.debug(f"Agent response in scenario {scenario_run_id}: {data}")
        
        # Handler for scenario events
        def handle_scenario_event(data):
            if data.get("scenario_run_id") == scenario_run_id:
                logger.info(f"Scenario {scenario_run_id} event: {data}")
        
        # Subscribe to relevant events
        event_bus.subscribe("agent.response", handle_agent_response)
        event_bus.subscribe("scenario.event", handle_scenario_event)
    
    async def run_scenario_sequence(
        self,
        scenario_run_id: int,
        event_sequence: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Run a predefined sequence of events in a scenario.
        
        Args:
            scenario_run_id: ID of the scenario run
            event_sequence: List of events to execute in order
            
        Returns:
            List of event results
        """
        results = []
        
        for i, event in enumerate(event_sequence):
            logger.info(f"Executing event {i+1}/{len(event_sequence)} in scenario {scenario_run_id}")
            
            result = await self.send_event_to_scenario(
                scenario_run_id,
                event.get("event_type", "custom"),
                event.get("data", {}),
                event.get("target_agent_id")
            )
            
            results.append(result)
            
            # Optional delay between events
            delay = event.get("delay_seconds", 0)
            if delay > 0:
                await asyncio.sleep(delay)
        
        return results
    
    async def shutdown(self):
        """
        Shutdown the ScenarioRunner and clean up all resources.
        """
        logger.info("ScenarioRunner shutting down...")
        
        # Stop all active scenarios
        active_scenario_ids = list(self.active_scenarios.keys())
        for scenario_id in active_scenario_ids:
            await self.stop_scenario(scenario_id)
        
        # Shutdown EngineManager
        await self.engine_manager.shutdown()
        
        logger.info("ScenarioRunner shutdown complete")


# Convenience function for quick scenario execution
async def run_scenario_from_template(
    db: Session,
    template_name: str,
    scenario_config: Optional[Dict[str, Any]] = None,
    agent_configs: Optional[List[Dict[str, Any]]] = None,
    event_sequence: Optional[List[Dict[str, Any]]] = None
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to run a complete scenario from start to finish.
    
    Args:
        db: Database session
        template_name: Name of the scenario template
        scenario_config: Optional scenario configuration
        agent_configs: Optional agent configurations
        event_sequence: Optional sequence of events to execute
        
    Returns:
        Dictionary containing scenario execution results
    """
    runner = ScenarioRunner(db)
    
    try:
        # Start scenario
        scenario_run_id = await runner.start_scenario(
            template_name, scenario_config, agent_configs
        )
        
        if not scenario_run_id:
            return {"error": "Failed to start scenario"}
        
        results = {"scenario_run_id": scenario_run_id, "events": []}
        
        # Run event sequence if provided
        if event_sequence:
            event_results = await runner.run_scenario_sequence(scenario_run_id, event_sequence)
            results["events"] = event_results
        
        # Get final status
        final_status = runner.get_scenario_status(scenario_run_id)
        results["final_status"] = final_status
        
        # Stop scenario
        await runner.stop_scenario(scenario_run_id)
        
        return results
        
    except Exception as e:
        logger.error(f"Error in run_scenario_from_template: {e}", exc_info=True)
        return {"error": str(e)}
    
    finally:
        await runner.shutdown()
