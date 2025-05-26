# pyscrai/engines/execution_pipeline.py

from typing import List, Dict, Any, Callable

class ExecutionPipeline:
    """
    Manages the sequential and potentially parallel execution of tasks within a scenario.
    This is a basic implementation and will be expanded for more complex flows.
    """
    def __init__(self):
        """Initializes the ExecutionPipeline."""
        self.pipeline_steps: List[Dict[str, Any]] = []
        self.current_step_index: int = -1
        print("ExecutionPipeline initialized.")

    def add_step(self, step_name: str, action: Callable[..., Any], parameters: Dict[str, Any] = None, 
                 is_parallel: bool = False, depends_on: List[str] = None):
        """
        Adds a step to the execution pipeline.
        Args:
            step_name (str): A unique name for this step.
            action (Callable[..., Any]): The function/method to execute for this step.
                                       It will receive `parameters` and potentially context.
            parameters (Dict[str, Any], optional): Parameters to pass to the action. Defaults to None.
            is_parallel (bool, optional): Whether this step can be run in parallel with others (not fully implemented).
                                        Defaults to False.
            depends_on (List[str], optional): Names of steps that must complete before this one starts (for future DAG execution).
                                            Defaults to None.
        """
        if not step_name:
            raise ValueError("Step name cannot be empty.")
        if not callable(action):
            raise TypeError("Action must be a callable function.")

        self.pipeline_steps.append({
            "name": step_name,
            "action": action,
            "parameters": parameters if parameters is not None else {},
            "is_parallel": is_parallel,
            "depends_on": depends_on if depends_on is not None else [],
            "status": "pending" # pending, running, completed, failed
        })
        print(f"Step '{step_name}' added to the pipeline.")

    def execute_step(self, step_details: Dict[str, Any], engines: Dict[str, Any], 
                     event_bus: Any, state_manager: Any) -> Any:
        """
        Executes a single step from the pipeline definition.
        This is a conceptual placeholder for how EngineManager might call a step.
        In a real scenario, this would be more integrated with the pipeline's own execution flow.

        Args:
            step_details (Dict[str, Any]): The definition of the step to execute.
                                           Should contain 'action', 'parameters'.
            engines (Dict[str, Any]): Available engines.
            event_bus (Any): The system event bus.
            state_manager (Any): The system state manager.
        Returns:
            The result of the step's action.
        """
        action = step_details.get("action")
        parameters = step_details.get("parameters", {})
        step_name = step_details.get("name", "Unnamed Step")

        if not callable(action):
            print(f"Error: Action for step '{step_name}' is not callable.")
            return None

        print(f"ExecutionPipeline: Executing step '{step_name}' with params: {parameters}")
        try:
            # The action might need access to engines, event_bus, or state_manager
            # This is a simplified call; a more robust system might pass a context object.
            result = action(**parameters, engines=engines, event_bus=event_bus, state_manager=state_manager)
            print(f"Step '{step_name}' completed successfully.")
            return result
        except Exception as e:
            print(f"Error executing step '{step_name}': {e}")
            # Potentially publish an error event via event_bus
            if event_bus:
                event_bus.publish(f"pipeline.step.error", {"step_name": step_name, "error": str(e)})
            return None

    def run_pipeline(self, engines: Dict[str, Any], event_bus: Any, state_manager: Any):
        """
        Runs all steps in the pipeline sequentially.
        Args:
            engines (Dict[str, Any]): Available engines.
            event_bus (Any): The system event bus.
            state_manager (Any): The system state manager.
        """
        print("ExecutionPipeline: Starting pipeline run...")
        if not self.pipeline_steps:
            print("Pipeline is empty. Nothing to run.")
            return

        for i, step in enumerate(self.pipeline_steps):
            self.current_step_index = i
            step["status"] = "running"
            print(f"\nRunning step {i+1}/{len(self.pipeline_steps)}: '{step['name']}'")
            
            try:
                # For now, we assume the action function is designed to accept these context arguments
                # or uses a **kwargs mechanism to ignore them if not needed.
                step_result = step["action"](
                    **(step["parameters"] if step["parameters"] else {}),
                    engines=engines,
                    event_bus=event_bus,
                    state_manager=state_manager
                )
                step["status"] = "completed"
                step["result"] = step_result # Store result if any
                print(f"Step '{step['name']}' finished. Result: {str(step_result)[:100]}")
                if event_bus:
                    event_bus.publish(f"pipeline.step.completed", {"step_name": step["name"], "result": step_result})
            except Exception as e:
                step["status"] = "failed"
                step["error"] = str(e)
                print(f"Error during step '{step['name']}': {e}. Halting pipeline.")
                if event_bus:
                    event_bus.publish(f"pipeline.step.failed", {"step_name": step["name"], "error": str(e)})
                # Basic error handling: stop pipeline on first error
                break 
        
        self.current_step_index = -1 # Reset after run
        print("\nExecutionPipeline: Pipeline run finished.")

    def get_pipeline_status(self) -> List[Dict[str, Any]]:
        """Returns the current status of all steps in the pipeline."""
        return self.pipeline_steps

if __name__ == '__main__':
    # This section is for basic testing and demonstration.
    print("Running ExecutionPipeline example...")
    pipeline = ExecutionPipeline()

    # Mock components for demonstration
    class MockEngineManager:
        def get_engine(self, name):
            print(f"MockEngineManager: get_engine({name}) called")
            return f"MockEngineInstance_{name}"
    
    class MockEventBus:
        def publish(self, event_type, data):
            print(f"MockEventBus: publish({event_type}, {data}) called")

    class MockStateManager:
        def update_state(self, key, value):
            print(f"MockStateManager: update_state({key}, {value}) called")

    mock_engines = MockEngineManager()
    mock_bus = MockEventBus()
    mock_state = MockStateManager()

    # Define some example actions
    def action_initialize(config_path: str, engines: Dict, event_bus: Any, state_manager: Any, **kwargs):
        print(f"Action: Initializing with config: {config_path}")
        state_manager.update_state("initialized", True)
        event_bus.publish("initialization.complete", {"config": config_path})
        return {"status": "initialized", "path": config_path}

    def action_process_data(data_source: str, engines: Dict, event_bus: Any, state_manager: Any, **kwargs):
        print(f"Action: Processing data from: {data_source}")
        actor_engine = engines.get_engine("ActorEngine") # Conceptual
        print(f"  Using engine: {actor_engine}")
        processed_data = f"processed_{data_source}"
        state_manager.update_state("last_processed", processed_data)
        return {"processed_data": processed_data}

    def action_analyze_results(results: Any, engines: Dict, event_bus: Any, state_manager: Any, **kwargs):
        print(f"Action: Analyzing results: {results}")
        analyst_engine = engines.get_engine("AnalystEngine") # Conceptual
        print(f"  Using engine: {analyst_engine}")
        analysis = f"analysis_of_{results.get('processed_data', 'unknown_data')}"
        event_bus.publish("analysis.complete", {"analysis": analysis})
        return {"analysis_summary": analysis}

    def action_cleanup(engines: Dict, event_bus: Any, state_manager: Any, **kwargs):
        print(f"Action: Cleaning up resources.")
        state_manager.update_state("cleaned_up", True)
        return {"status": "cleanup_complete"}

    # Add steps to the pipeline
    pipeline.add_step(
        step_name="InitializeSystem", 
        action=action_initialize, 
        parameters={"config_path": "/path/to/scenario.cfg"}
    )
    pipeline.add_step(
        step_name="ProcessCoreData", 
        action=action_process_data, 
        parameters={"data_source": "input_file.dat"}
    )
    # This step depends on the output of the previous one, conceptually.
    # A more advanced pipeline would handle data passing between steps explicitly.
    # For now, we assume state_manager or direct return values might be used.
    # The current `run_pipeline` passes the direct return of a step to the next if designed so,
    # but this example's actions are not chained that way; they use state_manager or fixed params.

    # To demonstrate data passing, let's modify how `action_analyze_results` gets its input.
    # The `run_pipeline` method would need to be smarter to pass output of one step as input to another.
    # For this basic example, we'll assume `action_analyze_results` can access prior results via `state_manager`
    # or that `EngineManager` would orchestrate this data flow when calling individual steps.
    # The current `run_pipeline` example is simplified.

    # Let's make a step that explicitly uses the output of a previous one (conceptual)
    # This requires the `run_pipeline` to be more sophisticated or the `EngineManager` to handle it.
    # For now, we'll just add the step as is.
    pipeline.add_step(
        step_name="AnalyzeProcessedData",
        action=action_analyze_results,
        # `results` would ideally be the output of "ProcessCoreData"
        # This basic pipeline doesn't automatically wire outputs to inputs.
        # We'll simulate it by having `action_analyze_results` fetch from `state_manager` if needed,
        # or assume `EngineManager` handles this data flow if calling steps individually.
        parameters={"results": {"processed_data": "placeholder_from_previous_step"}} # Placeholder
    )
    pipeline.add_step(
        step_name="FinalCleanup",
        action=action_cleanup
    )

    # Run the entire pipeline
    pipeline.run_pipeline(engines=mock_engines, event_bus=mock_bus, state_manager=mock_state)

    # Get pipeline status
    print("\nFinal pipeline status:")
    for step_status in pipeline.get_pipeline_status():
        print(f"  - {step_status['name']}: {step_status['status']}")
        if 'error' in step_status:
            print(f"    Error: {step_status['error']}")

    print("\nExecutionPipeline example finished.")
