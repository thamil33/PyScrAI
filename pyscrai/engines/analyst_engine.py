# pyscrai/engines/analyst_engine.py
"""
AnalystEngine for PyScrAI.

This engine is responsible for analyzing simulation results, detecting patterns,
and providing insights. It extends the BaseEngine and utilizes an
Agno Agent for LLM interactions, configured with an analytical focus.
"""
import asyncio
import logging
import json 
import os
from typing import Any, Dict, List, Optional

from agno.agent import Agent # Base Agent for type hinting
from agno.models.message import Message
from agno.run.response import RunResponse # To type hint agent responses

# Assuming BaseEngine is in the same directory or a discoverable path
from .base_engine import BaseEngine
# from ..databases.models.schemas import QueuedEventResponse, EventStatusUpdate # For future use

# Initialize a logger for this module
logger = logging.getLogger(__name__)

class AnalystEngine(BaseEngine):
    """
    AnalystEngine for result analysis and pattern detection.

    Attributes:
        analytical_focus (Optional[str]): A description of the analyst's
                                          specific focus or the types of
                                          patterns it should look for.
    """
    
    async def initialize(self, register_with_server: bool = True) -> None:
        """
        Initializes the AnalystEngine, including the underlying Agno agent
        and its analytical configuration.

        Args:
            register_with_server (bool): Whether to register the engine with the server.
        """
        if self.initialized:
            self.logger.info(f"AnalystEngine '{self.engine_name}' already initialized.")
            return

        # Call the parent's initialize method, passing the argument
        await super().initialize(register_with_server=register_with_server)
        
        if self.agent:
            self._configure_agent_for_analysis() # Ensure this method exists and is correctly named
            self.logger.info(f"AnalystEngine '{self.engine_name}' fully initialized.")
        else:
            self.logger.error(f"Agent not initialized in BaseEngine for AnalystEngine '{self.engine_name}'. Analysis focus not configured.")
        # self.initialized is set by BaseEngine

    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "AnalystEngine",
        description: Optional[str] = "Analyzes simulation data and identifies patterns.",
        analytical_focus: Optional[str] = "General data analysis and insight generation.",
        storage_path: Optional[str] = None,
        model_provider: str = "openrouter",
        **kwargs: Any,
    ):
        """
        Initializes the AnalystEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the Agno Agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            analytical_focus (Optional[str]): Specific focus for the analysis.
            storage_path (Optional[str]): Path for the agent's storage.
            model_provider (str): The provider for the LLM model.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent_config=agent_config,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            engine_type="Analyst", # Explicitly set engine type
            storage_path=storage_path,
            model_provider=model_provider,
            **kwargs,
        )
        self.analytical_focus: Optional[str] = analytical_focus
        
        # Store analyst-specific attributes in the shared state
        self.state["analytical_focus"] = self.analytical_focus
        
        logger.info(f"AnalystEngine '{self.engine_name}' configured with focus: '{self.analytical_focus}'. Call initialize() to activate.")

    async def initialize(self, register_with_server: bool = True) -> None: 
        """
        Initializes the AnalystEngine, including the underlying Agno agent
        and its analytical configuration.

        Args:
            register_with_server (bool): Whether to register the engine with the server.
        """
        if self.initialized:
            logger.info(f"AnalystEngine '{self.engine_name}' already initialized.")
            return

        await super().initialize(register_with_server=register_with_server) 
        
        if self.agent:
            self._configure_agent_for_analysis()
            logger.info(f"AnalystEngine '{self.engine_name}' fully initialized.")
        else:
            logger.error(f"Agent initialization failed for AnalystEngine '{self.engine_name}'. Analysis focus not configured.")

    def _configure_agent_for_analysis(self) -> None:
        """
        Configures the underlying Agno Agent for analytical tasks based on `analytical_focus`.
        This method should be called after the agent has been initialized.
        """
        if not self.agent:
            logger.warning(f"Agno agent not available for {self.engine_name}. Cannot configure for analysis.")
            return

        base_system_message_content = ""
        if self.agent.system_message:
            if isinstance(self.agent.system_message, Message):
                base_system_message_content = self.agent.system_message.get_content_as_str()
            elif callable(self.agent.system_message):
                try:
                    base_system_message_content = self.agent.system_message(agent=self.agent)
                except TypeError:
                    base_system_message_content = self.agent.system_message()
            else:
                base_system_message_content = str(self.agent.system_message)

        analysis_prompt = "You are an AI Analyst. Your primary role is to meticulously examine provided data, identify significant patterns, detect anomalies, and generate concise, actionable insights."
        if self.analytical_focus:
            analysis_prompt += f" Your specific analytical focus is: {self.analytical_focus}."
        analysis_prompt += " Present your findings clearly, objectively, and support them with data-driven conclusions where possible. Provide structured output if appropriate (e.g., summaries, key findings as bullet points)."

        if base_system_message_content and base_system_message_content.strip():
            self.agent.system_message = f"{analysis_prompt}\n\nOriginal context: {base_system_message_content}"
        else:
            self.agent.system_message = analysis_prompt
        
        logger.info(f"Configured agent for analysis for {self.engine_name} with focus: {self.analytical_focus}.")
        logger.debug(f"New system message for {self.engine_name}: {self.agent.system_message}")

    def _setup_tools(self) -> List[Any]:
        """
        Sets up tools specific to the AnalystEngine.
        For example, tools for data manipulation, statistical analysis, or visualization.
        Currently, no analyst-specific tools are defined.

        Returns:
            List[Any]: An empty list of tools.
        """
        logger.debug(f"AnalystEngine '{self.engine_name}' setup tools: None")
        return []

    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an event payload by analyzing the provided data.

        Args:
            event_payload (Dict[str, Any]): Data to be analyzed.
                                         Expected to contain 'data_to_analyze'.
                                         This could be text, logs, or structured data (as a string or dict).
            **kwargs: Additional keyword arguments for the Agno Agent's arun method.

        Returns:
            Dict[str, Any]: A dictionary containing the 'content' of the analysis
                            and any 'error' messages.
        """
        if not self.initialized or not self.agent:
            logger.error(f"AnalystEngine '{self.engine_name}' not initialized. Cannot process event.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(f"{self.engine_name} processing event payload for analysis.")
        logger.debug(f"Event payload: {event_payload}")

        data_to_analyze = event_payload.get("data_to_analyze")
        if not data_to_analyze:
            logger.warning("No 'data_to_analyze' found in event_payload for AnalystEngine.")
            return {"content": None, "error": "No data_to_analyze provided in event payload"}

        if isinstance(data_to_analyze, (dict, list)):
            try:
                data_to_analyze_str = json.dumps(data_to_analyze, indent=2)
            except TypeError:
                data_to_analyze_str = str(data_to_analyze)
        else:
            data_to_analyze_str = str(data_to_analyze)
            
        message_to_agent = f"Please analyze the following data based on your configured focus:\n\n---\nDATA START\n---\n{data_to_analyze_str}\n---\nDATA END\n---\n\nProvide your insights and findings."

        try:
            response: Optional[RunResponse] = await self.agent.arun(message=message_to_agent, **kwargs)
            
            if response and response.content:
                logger.debug(f"{self.engine_name} raw analysis response: {response.content[:200]}...") 
                return {"content": response.content, "error": None}
            else:
                logger.warning(f"{self.engine_name} produced no content in analysis response.")
                return {"content": None, "error": "Agent produced no content during analysis"}
        except Exception as e:
            logger.error(f"Error during {self.engine_name} analysis run: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

async def main_analyst_example():
    """Example usage of the AnalystEngine."""
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("OPENROUTER_API_KEY"):
        # Note: For OpenRouter, OPENROUTER_API_KEY is the primary env var.
        # OPENAI_API_KEY might be checked by some underlying libraries if not careful,
        # but for OpenRouter provider, OPENROUTER_API_KEY is what Agno's OpenRouter model uses.
        # If using a free model, the key might not be strictly validated for all free models,
        # but it's good practice to have it set (even to a dummy value like "<y_bin_235>" for some free tiers).
        logger.warning("OPENROUTER_API_KEY (or OPENAI_API_KEY as a fallback for some tools) not found. Free models might work without it, but it's recommended to set it.")
        # For OpenRouter free tiers, often any non-empty string is fine for OPENROUTER_API_KEY
        # For this example, we'll proceed if it's not set, relying on free model access.

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    analyst_agent_config = {
        "model_config": {
            "id": "mistralai/mistral-7b-instruct:free", # Updated to a free model
            "temperature": 0.5,
        },
        "personality_config": {
            "name": "Insightful Analyst",
            "description": "An AI agent specialized in data analysis.",
            "instructions": "You are a helpful AI assistant.", 
        },
    }

    data_analyst = AnalystEngine(
        agent_config=analyst_agent_config,
        engine_name="TrendSpotterEngine",
        analytical_focus="Identifying emerging trends and anomalies in financial transaction logs.",
        description="Analyzes financial data to spot trends and anomalies.",
        storage_path="analyst_engine_storage.db",
        model_provider="openrouter" 
    )

    # Ensure OPENROUTER_API_KEY is set, even if to a dummy for free models,
    # as Agno's OpenRouter class might expect it.
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.info("OPENROUTER_API_KEY not set, using a dummy key for example with free model.")
        os.environ["OPENROUTER_API_KEY"] = "sk-or-v1-dummy-key-for-free-tier"


    await data_analyst.initialize()

    if not data_analyst.initialized or not data_analyst.agent:
        logger.error("Failed to initialize data_analyst. Exiting example.")
        return

    sample_financial_data = [
        {"timestamp": "2023-10-01T10:00:00Z", "transaction_id": "T1001", "amount": 150.75, "category": "electronics"},
        {"timestamp": "2023-10-01T10:05:00Z", "transaction_id": "T1002", "amount": 25.50, "category": "groceries"},
        {"timestamp": "2023-10-01T11:15:00Z", "transaction_id": "T1003", "amount": 3000.00, "category": "travel"},
        {"timestamp": "2023-10-02T14:30:00Z", "transaction_id": "T1004", "amount": 12.00, "category": "coffee"},
        {"timestamp": "2023-10-02T16:00:00Z", "transaction_id": "T1005", "amount": 140.00, "category": "electronics"},
        {"timestamp": "2023-10-03T09:00:00Z", "transaction_id": "T1006", "amount": 22.00, "category": "groceries"},
        {"timestamp": "2023-10-03T18:00:00Z", "transaction_id": "T1007", "amount": 7500.00, "category": "investment_ संदिग्ध"}, 
    ]
    event_payload_analysis = {"data_to_analyze": sample_financial_data}
    
    logger.info(f"\n--- Simulating analysis event for {data_analyst.engine_name} ---")
    analysis_result = await data_analyst.process(event_payload_analysis)

    if analysis_result["content"]:
        logger.info(f"\n{data_analyst.engine_name} reports:\n{analysis_result['content']}")
    else:
        logger.error(f"\n{data_analyst.engine_name} had no analysis or an error occurred: {analysis_result['error']}")

    exported_state = data_analyst.export_state()
    logger.info(f"\n--- Exported AnalystEngine State ---\n{exported_state}")

    new_analyst_config = analyst_agent_config.copy()
    loaded_analyst = AnalystEngine(
        agent_config=new_analyst_config,
        storage_path="loaded_analyst_storage.db" 
    )
    loaded_analyst.import_state(exported_state) 
    await loaded_analyst.initialize() 

    logger.info(f"Loaded analyst focus: {loaded_analyst.state.get('analytical_focus')}")
    logger.info(f"Loaded analyst system prompt: {loaded_analyst.agent.system_message if loaded_analyst.agent else 'Agent not loaded'}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    asyncio.run(main_analyst_example())
