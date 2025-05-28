"""
Engine Manager for PyScrAI orchestration system.
Integrates with AgentRuntime to manage engine lifecycle and coordination.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from .event_bus import EventBus
from .execution_pipeline import ExecutionPipeline
from .state_manager import StateManager
from ..agent_runtime import AgentRuntime

logger = logging.getLogger(__name__)


class EngineManager:
    """
    Central coordinator for all engines in the PyScrAI framework.
    Responsible for managing the lifecycle and interaction of different engines
    during a scenario execution. Now integrated with AgentRuntime.
    """
    def __init__(self, db: Session, storage_base_path: str = "./data/agent_storage"):
        """
        Initializes the EngineManager with orchestration components.
        
        Args:
            db: Database session for agent operations
            storage_base_path: Base path for agent storage files
        """
        self.db = db
        self.storage_base_path = storage_base_path
        
        # Initialize orchestration components
        self.event_bus = EventBus()
        self.execution_pipeline = ExecutionPipeline()
        self.state_manager = StateManager()
        
        # Initialize AgentRuntime for engine management
        self.agent_runtime = AgentRuntime(db, storage_base_path)
        
        # Track engines managed by this instance
        self.engines: Dict[str, Any] = {}
        self.scenario_engines: Dict[str, List[int]] = {}  # scenario_id -> [agent_instance_ids]
        
        logger.info("EngineManager initialized with full orchestration system.")

    def register_engine(self, engine_name: str, engine_instance):
        """
        Registers an engine instance with the manager.
        Args:
            engine_name (str): The unique name for the engine.
            engine_instance: The instance of the engine to register.
        """
        if not engine_name:
            raise ValueError("Engine name cannot be empty.")
        if engine_name in self.engines:
            # Potentially log a warning or raise a more specific error
            print(f"Warning: Engine '{engine_name}' is already registered. Overwriting.")
        self.engines[engine_name] = engine_instance
        print(f"Engine '{engine_name}' registered.")

    def unregister_engine(self, engine_name: str):
        """
        Unregisters an engine instance from the manager.
        Args:
            engine_name (str): The name of the engine to unregister.
        Returns:
            The engine instance if found and removed, otherwise None.
        """
        if engine_name in self.engines:
            print(f"Engine '{engine_name}' unregistered.")
            return self.engines.pop(engine_name)
        else:
            print(f"Warning: Engine '{engine_name}' not found for unregistration.")
            return None

    def get_engine(self, engine_name: str):
        """
        Retrieves a registered engine by its name.
        Args:
            engine_name (str): The name of the engine to retrieve.
        Returns:
            The engine instance if found, otherwise None.
        """
        engine = self.engines.get(engine_name)
        if not engine:
            print(f"Warning: Engine '{engine_name}' not found.")
        return engine

    def set_event_bus(self, event_bus_instance):
        """Sets the event bus for inter-engine communication."""
        self.event_bus = event_bus_instance
        print("Event bus set for EngineManager.")

    def set_execution_pipeline(self, pipeline_instance):
        """Sets the execution pipeline for orchestrating tasks."""
        self.execution_pipeline = pipeline_instance
        print("Execution pipeline set for EngineManager.")

    def set_state_manager(self, state_manager_instance):
        """Sets the state manager for tracking scenario state."""
        self.state_manager = state_manager_instance
        print("State manager set for EngineManager.")

    def orchestrate_scenario_step(self, scenario_id: str, step_details: dict):
        """
        Orchestrates a single step of a scenario.
        This is a placeholder and will be significantly more complex.
        It will involve using the event bus, execution pipeline, and state manager.
        Args:
            scenario_id (str): The ID of the current scenario.
            step_details (dict): Details of the current step to execute.
        """
        print(f"EngineManager: Orchestrating step for scenario '{scenario_id}': {step_details.get('action', 'N/A')}")
        # TODO: Implement detailed logic using event_bus, execution_pipeline, state_manager
        if not self.execution_pipeline:
            print("Warning: Execution pipeline not set. Cannot orchestrate step.")
            return
        # Conceptual call:
        # self.execution_pipeline.execute_step(step_details, self.engines, self.event_bus, self.state_manager)
        pass

    def initialize_engines_for_scenario(self, scenario_config: dict):
        """
        Initializes and configures engines based on the scenario requirements.
        Args:
            scenario_config (dict): The configuration for the scenario.
        """
        print(f"EngineManager: Initializing engines for scenario '{scenario_config.get('name', 'Unnamed Scenario')}'.")
        # TODO: Implement logic to dynamically load/configure engines based on scenario_config
        pass

    async def start_scenario_execution(self, scenario_run_id: int, scenario_config: Dict[str, Any]) -> Dict[int, bool]:
        """
        Starts the execution of a full scenario using AgentRuntime.
        
        Args:
            scenario_run_id (int): The ID of the scenario run
            scenario_config (Dict[str, Any]): The full configuration of the scenario
            
        Returns:
            Dict[int, bool]: Results of starting each agent (agent_instance_id -> success)
        """
        logger.info(f"EngineManager: Starting execution for scenario run {scenario_run_id}")
        
        # Initialize scenario state
        self.state_manager.initialize_scenario_state(
            str(scenario_run_id), 
            scenario_config
        )
        
        # Start all agents for this scenario using AgentRuntime
        results = await self.agent_runtime.start_scenario_agents(scenario_run_id)
        
        # Track which agents are part of this scenario
        successful_agents = [agent_id for agent_id, success in results.items() if success]
        self.scenario_engines[str(scenario_run_id)] = successful_agents
        
        # Publish scenario start event
        self.event_bus.publish("scenario.started", {
            "scenario_run_id": scenario_run_id,
            "agent_results": results,
            "successful_agents": successful_agents
        })
        
        logger.info(f"Scenario {scenario_run_id} started with {len(successful_agents)} active agents")
        return results

    async def stop_scenario_execution(self, scenario_run_id: int) -> Dict[int, bool]:
        """
        Stops the execution of a scenario and cleans up resources.
        
        Args:
            scenario_run_id (int): The ID of the scenario run to stop
            
        Returns:
            Dict[int, bool]: Results of stopping each agent
        """
        logger.info(f"EngineManager: Stopping execution for scenario run {scenario_run_id}")
        
        # Stop all agents for this scenario
        results = await self.agent_runtime.stop_scenario_agents(scenario_run_id)
        
        # Clean up scenario state
        self.state_manager.delete_scenario_state(str(scenario_run_id))
        
        # Remove from tracking
        if str(scenario_run_id) in self.scenario_engines:
            del self.scenario_engines[str(scenario_run_id)]
        
        # Publish scenario stop event
        self.event_bus.publish("scenario.stopped", {
            "scenario_run_id": scenario_run_id,
            "agent_results": results
        })
        
        logger.info(f"Scenario {scenario_run_id} stopped")
        return results

    async def send_message_to_agent(
        self, 
        agent_instance_id: int, 
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to a specific agent through AgentRuntime.
        
        Args:
            agent_instance_id: ID of the target agent
            message: Message to send
            context: Additional context for the message
            
        Returns:
            Agent's response or None if failed
        """
        return await self.agent_runtime.send_message_to_agent(
            agent_instance_id, message, context
        )

    async def broadcast_to_scenario_agents(
        self,
        scenario_run_id: int,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[int, Optional[Dict[str, Any]]]:
        """
        Broadcast a message to all agents in a scenario.
        
        Args:
            scenario_run_id: ID of the scenario
            message: Message to broadcast
            context: Additional context
            
        Returns:
            Dictionary mapping agent_instance_id to response
        """
        results = {}
        scenario_key = str(scenario_run_id)
        
        if scenario_key in self.scenario_engines:
            for agent_id in self.scenario_engines[scenario_key]:
                response = await self.agent_runtime.send_message_to_agent(
                    agent_id, message, context
                )
                results[agent_id] = response
        
        return results

    def get_scenario_status(self, scenario_run_id: int) -> Dict[str, Any]:
        """
        Get the current status of a scenario execution.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            Dictionary containing scenario status information
        """
        scenario_key = str(scenario_run_id)
        
        # Get active agents
        active_agents = self.agent_runtime.list_active_agents()
        scenario_agents = [
            agent for agent in active_agents 
            if agent["agent_instance_id"] in self.scenario_engines.get(scenario_key, [])
        ]
        
        # Get scenario state
        scenario_state = self.state_manager.get_full_scenario_state(scenario_key)
        
        return {
            "scenario_run_id": scenario_run_id,
            "active_agents": scenario_agents,
            "scenario_state": scenario_state,
            "total_agents": len(scenario_agents)
        }

    async def shutdown(self):
        """
        Shutdown the EngineManager and clean up all resources.
        """
        logger.info("EngineManager shutting down...")
        
        # Stop all active scenarios
        for scenario_id in list(self.scenario_engines.keys()):
            await self.stop_scenario_execution(int(scenario_id))
        
        # Shutdown AgentRuntime
        await self.agent_runtime.shutdown()
        
        logger.info("EngineManager shutdown complete")

    async def register_scenario(self, scenario_run_id: int, agent_instances: List[Any]) -> None:
        """
        Register a scenario and its agent instances with the engine manager.
        
        Args:
            scenario_run_id: ID of the scenario run
            agent_instances: List of agent instances associated with this scenario
        """
        logger.info(f"Registering scenario {scenario_run_id} with {len(agent_instances)} agents")
        
        # Add to scenario engines tracking
        self.scenario_engines[str(scenario_run_id)] = [instance.id for instance in agent_instances]

        # Initialize agents with the agent runtime (await async startup)
        for instance in agent_instances:
            await self.agent_runtime.start_agent(instance)

        # Initialize scenario state
        self.state_manager.create_scenario_state(scenario_run_id)

        logger.info(f"Successfully registered scenario {scenario_run_id}")
        
    async def queue_event(
        self, 
        scenario_run_id: int, 
        event_type: str, 
        event_data: Dict[str, Any],
        source_agent_id: Optional[int] = None,
        target_agent_id: Optional[int] = None,
        priority: int = 5
    ) -> int:
        """
        Queue an event for processing in a scenario.
        
        Args:
            scenario_run_id: ID of the scenario run
            event_type: Type of event to queue
            event_data: Event payload/data
            source_agent_id: Optional ID of the source agent
            target_agent_id: Optional ID of the target agent
            priority: Event processing priority (1-10)
            
        Returns:
            ID of the created event instance
        """
        # Create event in database
        from ...databases.models import EventType, EventInstance
        
        # Get event type from database
        event_type_obj = self.db.query(EventType).filter(EventType.name == event_type).first()
        if not event_type_obj:
            raise ValueError(f"Event type '{event_type}' not found")
            
        # Create event instance
        event_instance = EventInstance(
            event_type_id=event_type_obj.id,
            scenario_run_id=scenario_run_id,
            agent_instance_id=target_agent_id,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            data=event_data,
            status="pending",
            priority=priority
        )
        
        self.db.add(event_instance)
        self.db.commit()
        self.db.refresh(event_instance)
        
        # Publish to event bus
        await self.event_bus.publish_event(
            event_type=event_type,
            event_data={
                "event_instance_id": event_instance.id,
                "scenario_run_id": scenario_run_id,
                "data": event_data,
                "source_agent_id": source_agent_id,
                "target_agent_id": target_agent_id
            }
        )
        
        logger.info(f"Queued event {event_instance.id} of type '{event_type}' for scenario {scenario_run_id}")
        return event_instance.id
        
    async def get_event_queue_stats(self, scenario_run_id: int) -> Dict[str, Any]:
        """
        Get statistics about the event queue for a scenario.
        
        Args:
            scenario_run_id: ID of the scenario run
            
        Returns:
            Dictionary with event queue statistics
        """
        from ...databases.models import EventInstance
        
        # Count events by status
        pending_count = self.db.query(EventInstance).filter(
            EventInstance.scenario_run_id == scenario_run_id,
            EventInstance.status == "pending"
        ).count()
        
        processing_count = self.db.query(EventInstance).filter(
            EventInstance.scenario_run_id == scenario_run_id,
            EventInstance.status == "processing"
        ).count()
        
        completed_count = self.db.query(EventInstance).filter(
            EventInstance.scenario_run_id == scenario_run_id,
            EventInstance.status == "completed"
        ).count()
        
        failed_count = self.db.query(EventInstance).filter(
            EventInstance.scenario_run_id == scenario_run_id,
            EventInstance.status == "failed"
        ).count()
        
        return {
            "pending": pending_count,
            "processing": processing_count,
            "completed": completed_count,
            "failed": failed_count,
            "total": pending_count + processing_count + completed_count + failed_count
        }
        
    async def cleanup_scenario(self, scenario_run_id: int) -> None:
        """
        Clean up resources associated with a scenario.
        
        Args:
            scenario_run_id: ID of the scenario to clean up
        """
        scenario_run_id_str = str(scenario_run_id)
        
        if scenario_run_id_str in self.scenario_engines:
            # Get agent instances
            agent_instance_ids = self.scenario_engines[scenario_run_id_str]
            
            # Unregister each agent
            for agent_id in agent_instance_ids:
                self.agent_runtime.stop_agent(agent_id)
                
            # Clean up scenario state
            self.state_manager.remove_scenario_state(scenario_run_id)
            
            # Remove from tracking
            del self.scenario_engines[scenario_run_id_str]
            
            logger.info(f"Cleaned up resources for scenario {scenario_run_id}")
        else:
            logger.warning(f"Scenario {scenario_run_id} not found in engine manager")

if __name__ == '__main__':
    # This section is for basic testing and demonstration.
    # It will be expanded or moved to a dedicated test file.
    print("Running EngineManager example...")
    manager = EngineManager()

    # Mock Engine for demonstration
    class MockEngine:
        def __init__(self, name: str):
            self.name = name
            print(f"MockEngine '{self.name}' created.")

        def process(self, data: any) -> str:
            print(f"MockEngine '{self.name}' processing: {data}")
            return f"{self.name} processed {data}"

    engine_alpha = MockEngine("AlphaEngine")
    engine_beta = MockEngine("BetaEngine")

    manager.register_engine("alpha", engine_alpha)
    manager.register_engine("beta", engine_beta)

    retrieved_engine = manager.get_engine("alpha")
    if retrieved_engine:
        retrieved_engine.process("sample_data_for_alpha")

    manager.unregister_engine("gamma") # Test unregistering a non-existent engine
    unregistered_beta = manager.unregister_engine("beta")
    if unregistered_beta:
        print(f"Successfully unregistered {unregistered_beta.name}")
    
    print(f"Current registered engines: {list(manager.engines.keys())}")

    example_scenario_config = {"name": "Test Scenario Alpha", "version": "1.0"}
    manager.start_scenario_execution(scenario_id="scn_test_001", scenario_config=example_scenario_config)
    manager.orchestrate_scenario_step(scenario_id="scn_test_001", step_details={"action": "InitialSetup", "param": "value"})
    
    print("EngineManager example finished.")
