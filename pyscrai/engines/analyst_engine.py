# pyscrai/engines/analyst_engine.py
"""
AnalystEngine for PyScrAI.

This engine is responsible for analyzing simulation results, detecting patterns,
and providing insights. It extends the BaseEngine and utilizes an
Agno Agent for LLM interactions.
"""
import os
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.message import Message
from agno.run.response import RunResponse
# Assuming BaseEngine is in the same directory or a discoverable path
from .base_engine import BaseEngine


class AnalystEngine(BaseEngine):
    """
    AnalystEngine for result analysis and pattern detection.

    Attributes:
        analytical_focus (Optional[str]): A description of the analyst's
                                          specific focus or the types of
                                          patterns it should look for.
    """

    def __init__(
        self,
        agent: Agent,
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "AnalystEngine",
        description: Optional[str] = "Analyzes simulation data and identifies patterns.",
        analytical_focus: Optional[str] = "General data analysis and insight generation.",
        **kwargs: Any,
    ):
        """
        Initializes the AnalystEngine.

        Args:
            agent (Agent): The Agno Agent to be used for LLM interactions.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            analytical_focus (Optional[str]): Specific focus for the analysis.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent=agent,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            **kwargs,
        )
        self.analytical_focus: Optional[str] = analytical_focus

        # Configure the underlying Agno Agent for analytical tasks
        self._configure_agent_for_analysis()

    def _configure_agent_for_analysis(self) -> None:
        """
        Configures the underlying Agno Agent for analytical tasks.
        """
        if self.agent is None:
            self.logger.warning("Agno agent not initialized. Cannot configure for analysis.")
            return

        base_system_message = self.agent.system_message or ""
        if isinstance(base_system_message, Message):
            base_system_message_content = base_system_message.get_content_as_str()
        elif callable(base_system_message):
            try:
                base_system_message_content = base_system_message(agent=self.agent)
            except TypeError:
                base_system_message_content = base_system_message()
        else:
            base_system_message_content = str(base_system_message)

        analysis_prompt = "You are an AI Analyst. Your role is to examine data, identify patterns, anomalies, and provide concise insights."
        if self.analytical_focus:
            analysis_prompt += f" Your specific focus is: {self.analytical_focus}."
        analysis_prompt += " Present your findings clearly and objectively. If possible, provide data-driven conclusions."

        if base_system_message_content:
            self.agent.system_message = f"{analysis_prompt}\n\n{base_system_message_content}"
        else:
            self.agent.system_message = analysis_prompt
        
        self.logger.info(f"Configured for analysis: {self.engine_name}.")
        self.logger.debug(f"New system message for AnalystEngine: {self.agent.system_message}")

    def process_event(
        self, event_type: str, event_data: Dict[str, Any], **kwargs: Any
    ) -> Optional[RunResponse]:
        """
        Processes an event by analyzing the provided data.

        Args:
            event_type (str): The type of event (e.g., "analyze_data_stream", "report_findings").
            event_data (Dict[str, Any]): Data to be analyzed.
                                         Expected to contain 'data_to_analyze'.
                                         This could be text, logs, structured data (as string).
            **kwargs: Additional keyword arguments for the Agno Agent's run method.

        Returns:
            Optional[RunResponse]: The analytical response from the Agno Agent.
        """
        self.logger.info(f"{self.engine_name} processing event: {event_type}")
        self.logger.debug(f"Event data: {event_data}")

        if self.agent is None:
            self.logger.error("Agno agent not initialized for AnalystEngine.")
            return None

        data_to_analyze = event_data.get("data_to_analyze")
        if not data_to_analyze:
            self.logger.warning("No 'data_to_analyze' found in event_data for AnalystEngine.")
            return None

        # The prompt here provides the data for analysis.
        # The analytical approach is guided by the agent's system message.
        message_to_agent = f"Analyze the following data and provide your findings:\n\n{data_to_analyze}"

        try:
            response = self.agent.run(message=message_to_agent, **kwargs)
            self.logger.debug(f"Analyst raw response: {response.content if response else 'None'}") # type: ignore
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error during {self.engine_name} run: {e}")
            return None

    async def aprocess_event(
        self, event_type: str, event_data: Dict[str, Any], **kwargs: Any
    ) -> Optional[RunResponse]:
        """
        Asynchronously processes an event by analyzing the provided data.

        Args:
            event_type (str): The type of event.
            event_data (Dict[str, Any]): Data to be analyzed.
            **kwargs: Additional keyword arguments for the Agno Agent's arun method.

        Returns:
            Optional[RunResponse]: The asynchronous analytical response.
        """
        self.logger.info(f"{self.engine_name} asynchronously processing event: {event_type}")
        self.logger.debug(f"Async event data: {event_data}")

        if self.agent is None:
            self.logger.error("Agno agent not initialized for AnalystEngine (async).")
            return None

        data_to_analyze = event_data.get("data_to_analyze")
        if not data_to_analyze:
            self.logger.warning("No 'data_to_analyze' found in event_data for AnalystEngine (async).")
            return None

        message_to_agent = f"Analyze the following data and provide your findings:\n\n{data_to_analyze}"

        try:
            response = await self.agent.arun(message=message_to_agent, **kwargs)
            self.logger.debug(f"Analyst async raw response: {response.content if response else 'None'}") # type: ignore
            return response # type: ignore
        except Exception as e:
            self.logger.error(f"Error during async {self.engine_name} run: {e}")
            return None

    def get_state(self) -> Dict[str, Any]:
        """
        Gets the current state of the AnalystEngine.

        Returns:
            Dict[str, Any]: The current state of the engine.
        """
        base_state = super().get_state()
        base_state.update(
            {
                "analytical_focus": self.analytical_focus,
                # Potentially add more analyst-specific state here
            }
        )
        return base_state

    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Loads the state into the AnalystEngine.

        Args:
            state (Dict[str, Any]): The state to load.
        """
        super().load_state(state)
        self.analytical_focus = state.get("analytical_focus", self.analytical_focus)
        self._configure_agent_for_analysis()
        self.logger.info(f"Loaded state for {self.engine_name}.")


if __name__ == "__main__":
    # This is a simple example of how to use the AnalystEngine.

    # --- Configuration ---
    # 1. Configure the LLM model
    try:
        from agno.models.openai import OpenAIChat
        if not os.getenv("OPENAI_API_KEY"):
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please set it to run this example: export OPENAI_API_KEY='your_key_here'")
            exit()
        llm_model = OpenAIChat(model="gpt-3.5-turbo")
    except ImportError:
        print("OpenAI library not found. Please install it: pip install openai")
        exit()
    except Exception as e:
        print(f"Failed to initialize OpenAI model: {e}")
        exit()
        
    # 2. Create an Agno Agent
    analyst_agent = Agent(
        model=llm_model,
        debug_mode=True,
        system_message="You are a data analyst." 
    )

    # 3. Create an AnalystEngine instance
    data_analyst = AnalystEngine(
        agent=analyst_agent,
        engine_name="DataInsightEngine",
        analytical_focus="Identifying trends in user engagement.",
        description="Analyzes user interaction logs to find engagement patterns.",
    )

    # --- Simulate an event ---
    print(f"\n--- Simulating event for {data_analyst.engine_name} ---")
    sample_log_data = """
    UserA, action:login, timestamp:2023-10-01T10:00:00Z
    UserB, action:login, timestamp:2023-10-01T10:05:00Z
    UserA, action:view_page, page:/home, timestamp:2023-10-01T10:01:00Z
    UserA, action:click_button, button:submit_form, timestamp:2023-10-01T10:02:00Z
    UserC, action:login, timestamp:2023-10-01T10:06:00Z
    UserB, action:view_page, page:/products, timestamp:2023-10-01T10:07:00Z
    UserA, action:logout, timestamp:2023-10-01T10:10:00Z
    UserB, action:view_page, page:/cart, timestamp:2023-10-01T10:08:00Z
    UserC, action:view_page, page:/home, timestamp:2023-10-01T10:09:00Z
    """
    event_data_analysis = {"data_to_analyze": sample_log_data}
    
    # Synchronous example
    response = data_analyst.process_event("analyze_interaction_logs", event_data_analysis)

    if response and response.content:
        print(f"\n{data_analyst.engine_name} reports:\n{response.content}")
    else:
        print(f"\n{data_analyst.engine_name} had no analysis or an error occurred.")

    # --- Example of saving and loading state (simplified) ---
    print("\n--- Saving and Loading State Example ---")
    current_state = data_analyst.get_state()
    print(f"Saved state: {current_state}")

    # Create a new engine instance and load state
    new_analyst_agent = Agent(model=llm_model)
    loaded_analyst = AnalystEngine(agent=new_analyst_agent) # engine_name will default
    loaded_analyst.load_state(current_state)
    print(f"Loaded analyst name: {loaded_analyst.engine_name}") # Default name
    print(f"Loaded analytical focus: {loaded_analyst.analytical_focus}")

    # Test the loaded analyst
    event_data_new_logs = {"data_to_analyze": "UserX, login, 11:00; UserY, login, 11:05; UserX, click_feature_A, 11:02"}
    loaded_response = loaded_analyst.process_event("analyze_new_logs", event_data_new_logs)
    if loaded_response and loaded_response.content:
        print(f"\nLoaded {loaded_analyst.engine_name} reports: {loaded_response.content}")
    else:
        print(f"\nLoaded {loaded_analyst.engine_name} had no analysis or an error occurred.")
        
    # Asynchronous example (requires an event loop to run)
    async def run_async_example():
        print(f"\n--- Simulating async event for {data_analyst.engine_name} ---")
        async_response = await data_analyst.aprocess_event("analyze_interaction_logs", event_data_analysis)
        if async_response and async_response.content:
            print(f"\nAsync {data_analyst.engine_name} reports:\n{async_response.content}")
        else:
            print(f"\nAsync {data_analyst.engine_name} had no analysis or an error occurred.")

    # To run the async example:
    # import asyncio
    # asyncio.run(run_async_example())

