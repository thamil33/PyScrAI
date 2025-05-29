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

from pyscrai.databases.models import ScenarioRun, ScenarioTemplate, AgentInstance, AgentTemplate
from pyscrai.factories.scenario_factory import ScenarioFactory
from pyscrai.engines.orchestration.engine_manager import EngineManager

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
    ) -> int:
        """
        Start a new scenario execution from a template.
        
        Args:
            template_name: Name of the scenario template to use
            scenario_config: Optional runtime configuration for the scenario
            agent_configs: Optional configurations for specific agents
            
        Returns:
            ID of the created scenario run
        """
        logger.info(f"Starting scenario from template: {template_name}")
        
        try:
            # Load template from database by name
            template = self.db.query(ScenarioTemplate).filter(
                ScenarioTemplate.name == template_name
            ).first()
            
            if not template:
                raise ValueError(f"Scenario template '{template_name}' not found")
            
            # Create a new scenario run using the factory
            run_name = f"{template_name}_run_{asyncio.get_event_loop().time()}"
            scenario_run = self.scenario_factory.create_scenario_run(
                template_id=template.id,
                run_name=run_name,
                runtime_config=scenario_config or {}
            )
            
            # Update the scenario status to 'initializing'
            scenario_run.status = "initializing"
            self.db.commit()
            
            # Create agent instances based on the template's agent roles
            agent_instances = []
            for role, agent_config in template.agent_roles.items():
                # Get the specified agent template
                agent_template_name = agent_config.get("template_name")
                if not agent_template_name:
                    raise ValueError(f"Agent role '{role}' missing template_name")
                
                agent_template = self.db.query(AgentTemplate).filter(
                    AgentTemplate.name == agent_template_name
                ).first()
                
                if not agent_template:
                    raise ValueError(f"Agent template '{agent_template_name}' not found")
                
                # Apply any runtime overrides from agent_configs
                runtime_config = agent_config.get("config", {})
                if agent_configs and role in agent_configs:
                    runtime_config.update(agent_configs[role])
                
                # Create the agent instance
                instance = self.scenario_factory.agent_factory.create_agent_instance(
                    template_id=agent_template.id,
                    scenario_run_id=scenario_run.id,
                    instance_name=f"{role}_{agent_template.name}",
                    runtime_config=runtime_config
                )
                
                agent_instances.append(instance)
                logger.info(f"Created agent instance {instance.id} for role '{role}'")
            
            # Track as active scenario BEFORE initializing execution
            self.active_scenarios[scenario_run.id] = {
                "scenario_run": scenario_run,
                "agent_instances": agent_instances
            }

            # Register this scenario with the engine manager for orchestration (await async)
            await self.engine_manager.register_scenario(scenario_run.id, agent_instances)

            # Start the scenario execution
            await self._initialize_scenario_execution(scenario_run.id)
            
            # Update scenario status to 'running'
            import datetime
            scenario_run.status = "running"
            scenario_run.started_at = datetime.datetime.now()
            self.db.commit()
            
            logger.info(f"Scenario run {scenario_run.id} started successfully")
            return scenario_run.id
            
        except Exception as e:
            logger.error(f"Failed to start scenario: {e}", exc_info=True)
            raise
    
    async def stop_scenario(self, scenario_run_id: int, reason: str = "user_terminated") -> None:
        """
        Gracefully stop a running scenario.
        
        Args:
            scenario_run_id: ID of the scenario to stop
            reason: Reason for stopping the scenario
        """
        if scenario_run_id not in self.active_scenarios:
            logger.warning(f"Scenario {scenario_run_id} is not active and cannot be stopped")
            return
            
        logger.info(f"Stopping scenario {scenario_run_id}: {reason}")
        
        # Take a final snapshot before stopping
        await self.save_state_snapshot(scenario_run_id)
        
        # Complete the scenario with terminated status
        await self.complete_scenario(
            scenario_run_id, 
            status="terminated",
            results={"termination_reason": reason}
        )
    
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
    
    async def _initialize_scenario_execution(self, scenario_run_id: int) -> None:
        """
        Initialize the execution of a scenario.
        
        Args:
            scenario_run_id: ID of the scenario run to initialize
        """
        if scenario_run_id not in self.active_scenarios:
            raise ValueError(f"Scenario run {scenario_run_id} not found in active scenarios")
            
        scenario_data = self.active_scenarios[scenario_run_id]
        scenario_run = scenario_data["scenario_run"]
        agent_instances = scenario_data["agent_instances"]
        
        logger.info(f"Initializing execution for scenario {scenario_run_id}")
        
        # Load scenario template for event flow and configuration
        scenario_template = self.db.query(ScenarioTemplate).filter(
            ScenarioTemplate.id == scenario_run.template_id
        ).first()
        
        
        if not scenario_template:
            raise ValueError(f"Failed to load scenario template for run {scenario_run_id}")
        
        # Setup initial event flow based on template
        if "initial_events" in scenario_template.event_flow:
            for event_config in scenario_template.event_flow["initial_events"]:
                # Create initial events in the database
                event_type_name = event_config.get("type")
                if not event_type_name:
                    logger.warning(f"Event in scenario {scenario_run_id} missing type")
                    continue
                
                # Queue events with the engine manager for processing
                await self.engine_manager.queue_event(
                    scenario_run_id=scenario_run_id,
                    event_type=event_type_name,
                    event_data=event_config.get("data", {}),
                    source_agent_id=event_config.get("source_agent_id"),
                    target_agent_id=event_config.get("target_agent_id"),
                    priority=event_config.get("priority", 5)
                )
                
        # Initialize environment state based on template and config
        initial_state = scenario_template.config.get("initial_state", {})
        if scenario_run.config and "initial_state" in scenario_run.config:
            # Override with any runtime state configuration
            initial_state.update(scenario_run.config["initial_state"])
            
        # Set up the scenario state in the engine manager
        self.engine_manager.state_manager.initialize_scenario_state(
            scenario_run_id, initial_state
        )
        
        logger.info(f"Scenario {scenario_run_id} initialized and ready to run")
    
    async def monitor_scenario(self, scenario_run_id: int) -> Dict[str, Any]:
        """
        Get the current status and state of a running scenario.
        
        Args:
            scenario_run_id: ID of the scenario run to monitor
            
        Returns:
            Status and state information for the scenario
        """
        if scenario_run_id not in self.active_scenarios:
            # Try to load from database if not in memory
            scenario_run = self.db.query(ScenarioRun).filter(
                ScenarioRun.id == scenario_run_id
            ).first()
            
            if not scenario_run:
                raise ValueError(f"Scenario run {scenario_run_id} not found")
                
            return {
                "id": scenario_run_id,
                "status": scenario_run.status,
                "started_at": scenario_run.started_at,
                "completed_at": scenario_run.completed_at,
                "results": scenario_run.results,
                "is_active": False
            }
        
        scenario_data = self.active_scenarios[scenario_run_id]
        scenario_run = scenario_data["scenario_run"]
        
        # Get current state from state manager
        current_state = self.engine_manager.state_manager.get_scenario_state(scenario_run_id)
        
        # Get event queue status
        event_stats = await self.engine_manager.get_event_queue_stats(scenario_run_id)
        
        return {
            "id": scenario_run_id,
            "status": scenario_run.status,
            "started_at": scenario_run.started_at,
            "completed_at": scenario_run.completed_at,
            "current_state": current_state,
            "event_stats": event_stats,
            "is_active": True
        }
    
    async def complete_scenario(self, scenario_run_id: int, status: str = "completed", results: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark a scenario as complete and persist its final state.
        
        Args:
            scenario_run_id: ID of the scenario to complete
            status: Final status ('completed', 'failed', 'terminated')
            results: Optional results to store with the scenario run
        """
        if scenario_run_id not in self.active_scenarios:
            raise ValueError(f"Scenario run {scenario_run_id} not found in active scenarios")
            
        scenario_data = self.active_scenarios[scenario_run_id]
        scenario_run = scenario_data["scenario_run"]
        
        logger.info(f"Completing scenario {scenario_run_id} with status '{status}'")
        
        # Update scenario run in database
        scenario_run.status = status
        scenario_run.completed_at = asyncio.get_event_loop().time()
        
        # Get final state from state manager
        final_state = self.engine_manager.state_manager.get_scenario_state(scenario_run_id)
        
        # Merge with provided results if any
        scenario_results = {
            "final_state": final_state
        }
        
        if results:
            scenario_results.update(results)
            
        scenario_run.results = scenario_results
        self.db.commit()
        
        # Clean up resources
        await self.engine_manager.cleanup_scenario(scenario_run_id)
        del self.active_scenarios[scenario_run_id]
        
        logger.info(f"Scenario {scenario_run_id} completed and persisted to database")
    
    async def load_scenario_from_db(self, scenario_run_id: int) -> Dict[str, Any]:
        """
        Load a scenario run from the database, including all related agent instances.
        Useful for resuming scenarios or analyzing completed runs.
        
        Args:
            scenario_run_id: ID of the scenario run to load
            
        Returns:
            Dictionary with scenario details and associated agent instances
        """
        scenario_run = self.db.query(ScenarioRun).filter(
            ScenarioRun.id == scenario_run_id
        ).first()
        
        if not scenario_run:
            raise ValueError(f"Scenario run {scenario_run_id} not found")
            
        # Load associated agent instances
        agent_instances = self.db.query(AgentInstance).filter(
            AgentInstance.scenario_run_id == scenario_run_id
        ).all()
        
        # Load template to get full context
        scenario_template = self.db.query(ScenarioTemplate).filter(
            ScenarioTemplate.id == scenario_run.template_id
        ).first()
        
        if not scenario_template:
            logger.warning(f"Template not found for scenario run {scenario_run_id}")
        
        return {
            "scenario_run": scenario_run,
            "template": scenario_template,
            "agent_instances": agent_instances
        }
    
    async def resume_scenario(self, scenario_run_id: int) -> bool:
        """
        Resume a paused or interrupted scenario.
        
        Args:
            scenario_run_id: ID of the scenario to resume
            
        Returns:
            True if successfully resumed, False otherwise
        """
        # Check if scenario is already active
        if scenario_run_id in self.active_scenarios:
            logger.warning(f"Scenario {scenario_run_id} is already active")
            return False
            
        # Load scenario from database
        scenario_data = await self.load_scenario_from_db(scenario_run_id)
        scenario_run = scenario_data["scenario_run"]
        agent_instances = scenario_data["agent_instances"]
        
        # Check if scenario is in a resumable state
        if scenario_run.status in ["completed", "failed", "terminated"]:
            logger.warning(f"Cannot resume scenario {scenario_run_id} with status '{scenario_run.status}'")
            return False
            
        logger.info(f"Resuming scenario {scenario_run_id}")
        
        # Update status
        scenario_run.status = "resuming"
        self.db.commit()
        
        # Register with engine manager
        self.engine_manager.register_scenario(scenario_run.id, agent_instances)
        
        # Add to active scenarios
        self.active_scenarios[scenario_run_id] = {
            "scenario_run": scenario_run,
            "agent_instances": agent_instances
        }
        
        # Restore state from saved results if available
        if scenario_run.results and "state_snapshot" in scenario_run.results:
            self.engine_manager.state_manager.restore_scenario_state(
                scenario_run_id, scenario_run.results["state_snapshot"]
            )
            
        # Update status and continue
        scenario_run.status = "running"
        self.db.commit()
        
        logger.info(f"Scenario {scenario_run_id} successfully resumed")
        return True
    
    async def save_state_snapshot(self, scenario_run_id: int) -> None:
        """
        Save a snapshot of the current scenario state to the database.
        
        Args:
            scenario_run_id: ID of the scenario to snapshot
        """
        if scenario_run_id not in self.active_scenarios:
            logger.warning(f"Cannot snapshot inactive scenario {scenario_run_id}")
            return
            
        scenario_data = self.active_scenarios[scenario_run_id]
        scenario_run = scenario_data["scenario_run"]
        
        # Get current state from state manager
        current_state = self.engine_manager.state_manager.get_scenario_state(scenario_run_id)
        
        # Update results with state snapshot
        if not scenario_run.results:
            scenario_run.results = {}
            
        scenario_run.results["state_snapshot"] = current_state
        scenario_run.results["last_snapshot_time"] = asyncio.get_event_loop().time()
        
        # Persist to database
        self.db.commit()
        logger.info(f"Saved state snapshot for scenario {scenario_run_id}")
    
    def list_scenarios(self, status_filter: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List scenarios from the database with optional filtering.
        
        Args:
            status_filter: Optional status to filter by
            limit: Maximum number of scenarios to return
            
        Returns:
            List of scenario data dictionaries
        """
        query = self.db.query(ScenarioRun)
        
        if status_filter:
            query = query.filter(ScenarioRun.status == status_filter)
            
        query = query.order_by(ScenarioRun.created_at.desc()).limit(limit)
        scenario_runs = query.all()
        
        results = []
        for run in scenario_runs:
            # Get template name
            template = self.db.query(ScenarioTemplate).filter(
                ScenarioTemplate.id == run.template_id
            ).first()
            
            template_name = template.name if template else "Unknown Template"
            
            # Get agent count
            agent_count = self.db.query(AgentInstance).filter(
                AgentInstance.scenario_run_id == run.id
            ).count()
            
            results.append({
                "id": run.id,
                "name": run.name,
                "template_name": template_name,
                "status": run.status,
                "agent_count": agent_count,
                "created_at": run.created_at,
                "started_at": run.started_at,
                "completed_at": run.completed_at,
                "is_active": run.id in self.active_scenarios
            })
            
        return results
        

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
