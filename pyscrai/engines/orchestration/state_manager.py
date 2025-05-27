# pyscrai/engines/state_manager.py

from typing import Dict, Any, Optional
from threading import Lock

class StateManager:
    """
    Manages and tracks the state of scenarios and agents during execution.
    Provides a centralized place to store and retrieve state information.
    This is a basic implementation; a more robust version might use a database
    or a distributed cache for persistence and scalability.
    """
    def __init__(self):
        """Initializes the StateManager."""
        # scenario_id -> {state_key: value}
        self.scenario_states: Dict[str, Dict[str, Any]] = {}
        # agent_id -> {state_key: value} (could be part of scenario_states or separate)
        self.agent_states: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock() # For thread-safe operations on shared state
        print("StateManager initialized.")

    def create_scenario_state(self, scenario_id: int) -> None:
        """
        Create a new state container for a scenario.
        
        Args:
            scenario_id: ID of the scenario
        """
        with self._lock:
            scenario_key = str(scenario_id)
            if scenario_key not in self.scenario_states:
                self.scenario_states[scenario_key] = {}
                print(f"Created state container for scenario {scenario_id}")
    
    def initialize_scenario_state(self, scenario_id: int, initial_state: Dict[str, Any]) -> None:
        """
        Initialize a scenario's state with provided values.
        
        Args:
            scenario_id: ID of the scenario
            initial_state: Initial state values to set
        """
        with self._lock:
            scenario_key = str(scenario_id)
            if scenario_key not in self.scenario_states:
                self.scenario_states[scenario_key] = {}
                
            self.scenario_states[scenario_key].update(initial_state)
            print(f"Initialized state for scenario {scenario_id}")
    
    def update_scenario_state(self, scenario_id: str, key: str, value: Any):
        """
        Updates a specific key in the state for a given scenario.
        Args:
            scenario_id (str): The ID of the scenario whose state is to be updated.
            key (str): The key of the state variable to update.
            value (Any): The new value for the state variable.
        """
        if not scenario_id:
            raise ValueError("Scenario ID cannot be empty.")
        if not key:
            raise ValueError("State key cannot be empty.")
            
        with self._lock:
            if scenario_id not in self.scenario_states:
                # Initialize if not present, though ideally initialize_scenario_state is called first
                self.scenario_states[scenario_id] = {}
                print(f"Warning: Scenario '{scenario_id}' was not explicitly initialized. Initializing now.")
            self.scenario_states[scenario_id][key] = value
            print(f"Scenario '{scenario_id}' state updated: '{key}' = '{str(value)[:50]}...'")

    def get_scenario_state(self, scenario_id: int) -> Dict[str, Any]:
        """
        Get the current state of a scenario.
        
        Args:
            scenario_id: ID of the scenario
            
        Returns:
            Dictionary with the scenario's current state
        """
        with self._lock:
            scenario_key = str(scenario_id)
            if scenario_key not in self.scenario_states:
                return {}
                
            # Return a copy to avoid external modification
            return dict(self.scenario_states[scenario_key])
    
    def get_scenario_state(self, scenario_id: str, key: str, default: Any = None) -> Any:
        """
        Retrieves a specific key from the state of a given scenario.
        Args:
            scenario_id (str): The ID of the scenario.
            key (str): The key of the state variable to retrieve.
            default (Any, optional): The value to return if the key or scenario is not found. Defaults to None.
        Returns:
            Any: The value of the state variable, or the default value.
        """
        with self._lock:
            scenario_specific_state = self.scenario_states.get(scenario_id)
            if scenario_specific_state is None:
                return default
            return scenario_specific_state.get(key, default)

    def get_full_scenario_state(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the entire state dictionary for a given scenario.
        Args:
            scenario_id (str): The ID of the scenario.
        Returns:
            Optional[Dict[str, Any]]: The state dictionary, or None if the scenario is not found.
                                      Returns a copy to prevent direct modification of internal state.
        """
        with self._lock:
            if scenario_id in self.scenario_states:
                return self.scenario_states[scenario_id].copy()
            return None

    def update_scenario_state(self, scenario_id: int, state_updates: Dict[str, Any]) -> None:
        """
        Update a scenario's state with new values.
        
        Args:
            scenario_id: ID of the scenario
            state_updates: State values to update
        """
        with self._lock:
            scenario_key = str(scenario_id)
            if scenario_key not in self.scenario_states:
                self.scenario_states[scenario_key] = {}
                
            self.scenario_states[scenario_key].update(state_updates)
            print(f"Updated state for scenario {scenario_id}")
    
    def restore_scenario_state(self, scenario_id: int, state_snapshot: Dict[str, Any]) -> None:
        """
        Restore a scenario's state from a saved snapshot.
        
        Args:
            scenario_id: ID of the scenario
            state_snapshot: Snapshot of the state to restore
        """
        with self._lock:
            scenario_key = str(scenario_id)
            self.scenario_states[scenario_key] = dict(state_snapshot)
            print(f"Restored state for scenario {scenario_id}")
    
    def remove_scenario_state(self, scenario_id: int) -> None:
        """
        Remove a scenario's state from memory.
        
        Args:
            scenario_id: ID of the scenario
        """
        with self._lock:
            scenario_key = str(scenario_id)
            if scenario_key in self.scenario_states:
                del self.scenario_states[scenario_key]
                print(f"Removed state for scenario {scenario_id}")

    def delete_scenario_state(self, scenario_id: str):
        """
        Deletes the state for a given scenario, typically upon completion or cancellation.
        Args:
            scenario_id (str): The ID of the scenario whose state is to be deleted.
        """
        with self._lock:
            if scenario_id in self.scenario_states:
                del self.scenario_states[scenario_id]
                print(f"State for scenario '{scenario_id}' deleted.")
            else:
                print(f"Warning: No state found to delete for scenario '{scenario_id}'.")

    # Agent-specific state methods (can be expanded similarly)
    def update_agent_state(self, agent_id: str, scenario_id: str, key: str, value: Any):
        """
        Updates state for a specific agent, potentially namespaced by scenario.
        For simplicity, this example uses a global agent state, but in a multi-scenario
        environment, agent state might be tied to a scenario_id.
        Args:
            agent_id (str): The ID of the agent.
            scenario_id (str): The ID of the scenario the agent is part of (for context/namespacing).
            key (str): The state key to update.
            value (Any): The new value.
        """
        # This is a simplified agent state; could be nested under scenario_id
        # e.g., self.scenario_states[scenario_id]['agents'][agent_id][key] = value
        with self._lock:
            if agent_id not in self.agent_states:
                self.agent_states[agent_id] = {}
            self.agent_states[agent_id][key] = value
            print(f"Agent '{agent_id}' (Scenario '{scenario_id}') state updated: '{key}' = '{str(value)[:50]}...'")

    def get_agent_state(self, agent_id: str, scenario_id: str, key: str, default: Any = None) -> Any:
        """
        Retrieves state for a specific agent.
        Args:
            agent_id (str): The ID of the agent.
            scenario_id (str): The ID of the scenario (for context).
            key (str): The state key.
            default (Any, optional): Default value if key not found. Defaults to None.
        Returns:
            Any: The state value or default.
        """
        with self._lock:
            agent_specific_state = self.agent_states.get(agent_id)
            if agent_specific_state is None:
                return default
            return agent_specific_state.get(key, default)

if __name__ == '__main__':
    # This section is for basic testing and demonstration.
    print("Running StateManager example...")
    state_manager = StateManager()

    SCENARIO_A = "scenario_alpha_123"
    SCENARIO_B = "scenario_beta_456"

    # Initialize scenario states
    state_manager.initialize_scenario_state(SCENARIO_A, {"status": "pending", "round": 0})
    state_manager.initialize_scenario_state(SCENARIO_B)

    # Update scenario states
    state_manager.update_scenario_state(SCENARIO_A, "status", "running")
    state_manager.update_scenario_state(SCENARIO_A, "current_event", "WeatherChange")
    state_manager.update_scenario_state(SCENARIO_A, "round", 1)
    state_manager.update_scenario_state(SCENARIO_B, "active_participants", ["agent1", "agent2"])

    # Get specific state values
    status_a = state_manager.get_scenario_state(SCENARIO_A, "status")
    print(f"Status of {SCENARIO_A}: {status_a}")
    round_a = state_manager.get_scenario_state(SCENARIO_A, "round", default= -1)
    print(f"Round of {SCENARIO_A}: {round_a}")
    non_existent_key = state_manager.get_scenario_state(SCENARIO_A, "non_existent_key", default="not_found")
    print(f"Non_existent_key for {SCENARIO_A}: {non_existent_key}")

    # Get full state
    full_state_a = state_manager.get_full_scenario_state(SCENARIO_A)
    print(f"Full state of {SCENARIO_A}: {full_state_a}")
    full_state_c = state_manager.get_full_scenario_state("scenario_charlie_789") # Non-existent
    print(f"Full state of scenario_charlie_789: {full_state_c}")

    # Agent state example
    AGENT_1 = "agent_smith_007"
    state_manager.update_agent_state(AGENT_1, SCENARIO_A, "location", "Sector 7G")
    state_manager.update_agent_state(AGENT_1, SCENARIO_A, "mood", "curious")
    agent_loc = state_manager.get_agent_state(AGENT_1, SCENARIO_A, "location")
    print(f"Agent {AGENT_1} location in {SCENARIO_A}: {agent_loc}")

    # Delete scenario state
    state_manager.delete_scenario_state(SCENARIO_A)
    print(f"Full state of {SCENARIO_A} after deletion: {state_manager.get_full_scenario_state(SCENARIO_A)}")
    state_manager.delete_scenario_state("scenario_charlie_789") # Try deleting non-existent

    print("StateManager example finished.")
