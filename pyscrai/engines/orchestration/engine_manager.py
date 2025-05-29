"""
Engine Manager for PyScrAI orchestration system.
Integrates with AgentRuntime to manage engine lifecycle and coordination.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from pyscrai.engines.orchestration.event_bus import EventBus
from pyscrai.engines.orchestration.execution_pipeline import ExecutionPipeline
from pyscrai.engines.orchestration.state_manager import StateManager
from pyscrai.engines.agent_runtime import AgentRuntime

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
        
        # Store rich context for each active scenario
        self.scenario_context_data: Dict[int, Dict[str, Any]] = {}
        
        # Subscribe to agent action output events
        self.event_bus.subscribe("agent.action.output", self._handle_agent_action_output)
        
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
        Register a scenario and its agent instances with the EngineManager.
        
        Args:
            scenario_run_id: ID of the scenario run
            agent_instances: List of agent instances for this scenario
        """
        logger.info(f"Registering scenario {scenario_run_id} with {len(agent_instances)} agents")
        
        # Track agents for this scenario
        self.scenario_engines[str(scenario_run_id)] = [
            instance.id for instance in agent_instances
        ]
        
        # Create basic scenario context data structure
        self.scenario_context_data[scenario_run_id] = {
            "agent_instances": agent_instances,
            "agent_roles": {},      # Will map agent_instance_id -> role
            "role_agents": {},      # Will map role -> [agent_instance_ids]
            "actor_agents": [],     # Will store agent_instance_ids of actors
            "event_flow": {},       # Will store the scenario's event flow
            "current_turn": None,   # Current turn holder (for turn-based scenarios)
            "turn_history": []      # History of turns (agent_instance_ids)
        }
        
        # Start each agent with its appropriate engine
        for instance in agent_instances:
            logger.info(f"Starting agent {instance.id} for scenario {scenario_run_id}")
            await self.agent_runtime.start_agent(instance.id)
        
        logger.info(f"Scenario {scenario_run_id} registered with all agents started")
    
    async def setup_scenario_context(self, scenario_run_id: int, scenario_template: Dict[str, Any], agent_instances: List[Any]) -> None:
        """
        Setup rich scenario context based on the template and agent instances.
        
        Args:
            scenario_run_id: ID of the scenario run
            scenario_template: The full scenario template with event_flow
            agent_instances: List of agent instances for this scenario
        """
        if scenario_run_id not in self.scenario_context_data:
            logger.warning(f"Scenario {scenario_run_id} not found in context data. Creating entry.")
            self.scenario_context_data[scenario_run_id] = {}
        
        context = self.scenario_context_data[scenario_run_id]
        
        # Store event flow from template
        context["event_flow"] = scenario_template.get("event_flow", {})
        
        # Map agent instances to their roles based on scenario template agent_roles
        agent_roles = scenario_template.get("agent_roles", {})
        role_mapping = {}
        role_agents = {}
        actor_agents = []
        
        for instance in agent_instances:
            # Find this agent's role in the template
            for role, role_config in agent_roles.items():
                template_name = role_config.get("template_name")
                if instance.template.name == template_name:
                    # Map this agent to the role
                    role_mapping[instance.id] = role
                    if role not in role_agents:
                        role_agents[role] = []
                    role_agents[role].append(instance.id)
                    
                    # Track actor agents specifically
                    if role_config.get("engine_type") == "actor":
                        actor_agents.append(instance.id)
                    break
        
        context["agent_roles"] = role_mapping
        context["role_agents"] = role_agents
        context["actor_agents"] = actor_agents
        
        # Initialize turn tracking if this is a turn-based scenario
        interaction_rules = scenario_template.get("config", {}).get("interaction_rules", {})
        if interaction_rules.get("turn_based", False):
            # Set initial turn holder if there are actors
            if actor_agents:
                context["current_turn"] = actor_agents[0]  # Start with first actor
                context["turn_history"] = []
        
        logger.info(f"Scenario {scenario_run_id} context setup complete with {len(role_mapping)} mapped agents")
    
    async def _handle_agent_action_output(self, topic: str, event_payload: Dict[str, Any]) -> None:
        """
        Handle an action output event from an agent and route it to appropriate targets
        based on the scenario's event flow configuration.
        
        Args:
            topic: Event topic (e.g., "agent.action.output")
            event_payload: Event data including scenario_run_id, source_agent_id, etc.
        """
        scenario_run_id = event_payload.get("scenario_run_id")
        source_agent_id = event_payload.get("source_agent_id")
        output_type = event_payload.get("output_type")
        data = event_payload.get("data", {})
        
        logger.info(f"Handling agent action output from agent {source_agent_id} in scenario {scenario_run_id}")
        
        # Verify this scenario exists in our context data
        if scenario_run_id not in self.scenario_context_data:
            logger.error(f"Scenario {scenario_run_id} not found in context data")
            return
        
        context = self.scenario_context_data[scenario_run_id]
        
        # Find source agent's role
        source_role = context["agent_roles"].get(source_agent_id)
        if not source_role:
            logger.error(f"Agent {source_agent_id} has no role in scenario {scenario_run_id}")
            return
        
        # Verify turn-taking rules if applicable
        if context.get("current_turn") is not None:
            if context["current_turn"] != source_agent_id:
                logger.warning(f"Agent {source_agent_id} acted out of turn in scenario {scenario_run_id}")
                # Optionally: return or take some corrective action
        
        # Find the relevant event flow step based on agent role and output type
        event_flow = context.get("event_flow", {})
        event_step = None
        
        # Map the output_type to a relevant event_flow step
        for step_name, step_config in event_flow.items():
            if step_config.get("source") == source_role or step_config.get("source") == "any_actor" and source_role.endswith("_actor"):
                # Found a matching event step
                event_step = step_config
                event_step_name = step_name
                break
        
        if not event_step:
            logger.warning(f"No matching event flow step for role {source_role} with output {output_type}")
            return
        
        # Determine target agents based on event step configuration
        target = event_step.get("target", "")
        target_agent_ids = []
        
        if target == "all_agents":
            # Target all agents in the scenario
            target_agent_ids = [aid for aid in context["agent_roles"].keys()]
        elif target == "other_actors":
            # Target all actors except the source
            target_agent_ids = [aid for aid in context["actor_agents"] if aid != source_agent_id]
        elif target == "system":
            # System events might be logged or processed differently
            logger.info(f"System event from {source_role}: {output_type}")
            # No agent targets for system events
        elif target in context["role_agents"]:
            # Target a specific role
            target_agent_ids = context["role_agents"][target]
        
        # If this is a turn-based scenario, update the current turn
        if context.get("current_turn") is not None and target_agent_ids:
            # Find next actor in the sequence (simple round-robin)
            actors = context["actor_agents"]
            current_idx = actors.index(source_agent_id) if source_agent_id in actors else -1
            next_idx = (current_idx + 1) % len(actors) if actors else 0
            next_turn = actors[next_idx] if actors else None
            
            context["current_turn"] = next_turn
            context["turn_history"].append(source_agent_id)
        
        # Deliver the event to each target agent
        for target_id in target_agent_ids:
            logger.info(f"Delivering {output_type} event from {source_agent_id} to {target_id} in scenario {scenario_run_id}")
            
            # Prepare the event payload for the target
            event_data = {
                "source_agent_id": source_agent_id,
                "source_role": source_role,
                "event_type": output_type,
                "scenario_run_id": scenario_run_id,
                **data
            }
            
            # Deliver the event to the target agent
            await self.deliver_event_to_agent(target_id, output_type, event_data)
    
    async def deliver_event_to_agent(self, agent_id: int, event_type: str, event_data: Dict[str, Any]) -> bool:
        """
        Deliver an event directly to an agent's engine.
        
        Args:
            agent_id: ID of the target agent
            event_type: Type of event being delivered
            event_data: Event payload data
            
        Returns:
            True if event was delivered successfully, False otherwise
        """
        try:
            if agent_id not in self.agent_runtime.active_agents:
                logger.error(f"Agent {agent_id} is not active")
                return False
            
            runtime_info = self.agent_runtime.active_agents[agent_id]
            engine = runtime_info["engine"]
            
            # Call the engine's handle_event method
            if hasattr(engine, "handle_delivered_event") and callable(engine.handle_delivered_event):
                await engine.handle_delivered_event(event_type, event_data)
                return True
            else:
                logger.warning(f"Agent {agent_id}'s engine does not have handle_delivered_event method")
                return False
                
        except Exception as e:
            logger.error(f"Failed to deliver event to agent {agent_id}: {e}", exc_info=True)
            return False
    
    async def trigger_scenario_initialization(self, scenario_run_id: int) -> bool:
        """
        Trigger the initial events for a scenario based on its event_flow.
        
        Args:
            scenario_run_id: ID of the scenario to initialize
            
        Returns:
            True if initialization events were triggered successfully
        """
        if scenario_run_id not in self.scenario_context_data:
            logger.error(f"Scenario {scenario_run_id} not found in context data")
            return False
        
        context = self.scenario_context_data[scenario_run_id]
        event_flow = context.get("event_flow", {})
        
        # Look for the scenario_initialization event
        init_event = None
        for name, config in event_flow.items():
            if name == "scenario_initialization" or config.get("conditions", {}).get("trigger") == "scenario_start":
                init_event = config
                break
        
        if not init_event:
            logger.warning(f"No initialization event found for scenario {scenario_run_id}")
            return True  # Not a failure, might be intentional
        
        # Prepare the initialization event payload
        event_data = {
            "scenario_run_id": scenario_run_id,
            "source_agent_id": None,  # System-initiated
            "scenario_context": f"Scenario {scenario_run_id} has started",
            "initial_setting": {},  # Could be populated from scenario config
            "participant_roles": context["agent_roles"]
        }
        
        # Determine target agents
        target = init_event.get("target")
        target_agent_ids = []
        
        if target == "all_agents":
            target_agent_ids = list(context["agent_roles"].keys())
        elif target in context["role_agents"]:
            target_agent_ids = context["role_agents"][target]
        
        # Deliver the initialization event to each target
        success = True
        for agent_id in target_agent_ids:
            result = await self.deliver_event_to_agent(agent_id, "scenario_initialization", event_data)
            if not result:
                success = False
        
        return success

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
