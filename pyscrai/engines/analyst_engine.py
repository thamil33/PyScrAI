"""
AnalystEngine for PyScrAI.

This engine is responsible for analyzing scenarios, extracting insights,
and providing analytical perspectives on events and interactions.
"""
import logging
from typing import Any, Dict, List, Optional

from .base_engine import BaseEngine

# Initialize a logger for this module
logger = logging.getLogger(__name__)


class AnalystEngine(BaseEngine):
    """
    AnalystEngine for scenario analysis.

    Inherits from BaseEngine and implements analysis-specific logic,
    including data interpretation and insight generation.

    Attributes:
        analysis_focus (Optional[str]): The primary focus of analysis.
        metrics_tracked (List[str]): List of metrics this engine tracks.
    """
    
    def __init__(
        self,
        agent_config: Dict[str, Any],
        engine_id: Optional[str] = None,
        engine_name: Optional[str] = "AnalystEngine",
        description: Optional[str] = "Analyzes scenarios and provides insights.",
        analysis_focus: Optional[str] = None,  # Allow None to use default
        metrics_tracked: Optional[List[str]] = None,
        storage_path: Optional[str] = None,
        model_provider: str = "openai",
        **kwargs: Any,
    ):
        """
        Initializes the AnalystEngine.

        Args:
            agent_config (Dict[str, Any]): Configuration for the agent.
            engine_id (Optional[str]): A unique identifier for the engine.
            engine_name (Optional[str]): The name of the engine.
            description (Optional[str]): A brief description of the engine's purpose.
            analysis_focus (Optional[str]): The primary focus of analysis.
            metrics_tracked (Optional[List[str]]): List of metrics to track.
            storage_path (Optional[str]): Path for the agent's storage.
            model_provider (str): The provider for the LLM model.
            **kwargs: Additional keyword arguments to pass to the BaseEngine.
        """
        super().__init__(
            agent_config=agent_config,
            engine_id=engine_id,
            engine_name=engine_name,
            description=description,
            storage_path=storage_path,
            model_provider=model_provider,
            engine_type="Analyst",
            **kwargs,
        )
        self.analysis_focus: Optional[str] = analysis_focus or "behavioral patterns"  # Default to test expectation
        self.metrics_tracked: List[str] = metrics_tracked or [
            "interaction_count",
            "response_time",
            "sentiment_score",
            "complexity_level"
        ]
        
        # Store analyst-specific attributes in the shared state
        self.state["analysis_focus"] = self.analysis_focus
        self.state["metrics_tracked"] = self.metrics_tracked
        self.state["analysis_results"] = []

        logger.info(f"AnalystEngine '{self.engine_name}' configured with focus: {self.analysis_focus}")

    async def initialize(self) -> None:
        """
        Initializes the AnalystEngine.
        """
        if self.initialized:
            logger.info(f"AnalystEngine '{self.engine_name}' already initialized.")
            return

        await super().initialize()
        
        if self.initialized:
            logger.info(f"AnalystEngine '{self.engine_name}' fully initialized.")
        else:
            logger.error(f"AnalystEngine '{self.engine_name}' initialization failed.")

    def _setup_tools(self) -> List[Any]:
        """
        Sets up tools specific to the AnalystEngine.
        Currently, no analyst-specific tools are defined.

        Returns:
            List[Any]: An empty list of tools.
        """
        logger.debug(f"AnalystEngine '{self.engine_name}' setup tools: None")
        return []

    async def process(self, event_payload: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """
        Processes an event payload and generates analytical insights.

        Args:
            event_payload (Dict[str, Any]): Data associated with the event.
                                         Expected to contain data for analysis.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, Any]: A dictionary containing the analysis results ('content')
                            and any errors ('error').
        """
        if not self.initialized:
            logger.error(f"AnalystEngine '{self.engine_name}' not initialized.")
            return {"content": None, "error": "Engine not initialized"}

        logger.info(f"{self.engine_name} processing analytical event.")
        logger.debug(f"Event payload: {event_payload}")

        try:
            # Analyze the event payload
            analysis_result = self._analyze_event(event_payload)
            
            # Store the analysis result
            self.state["analysis_results"].append(analysis_result)
            
            # Generate analytical response using LLM
            try:
                from ..factories.llm_factory import get_llm_instance
                
                # Create analysis prompt
                analysis_prompt = self._create_analysis_prompt(event_payload, analysis_result)
                
                llm = get_llm_instance(provider=self.model_provider)
                ai_response = await llm.agenerate(analysis_prompt)
                
                # Extract content from AI response
                if hasattr(ai_response, 'content'):
                    response_content = f"[Analyst]: {ai_response.content}"
                elif isinstance(ai_response, str):
                    response_content = f"[Analyst]: {ai_response}"
                else:
                    response_content = f"[Analyst]: {str(ai_response)}"
                    
            except Exception as llm_error:
                logger.warning(f"LLM call failed for analyst: {llm_error}. Using fallback response.")
                # Fallback to simple response if LLM fails
                response_content = self._generate_analysis_response(analysis_result)
            
            logger.debug(f"Analysis response: {response_content}")
            return {"content": response_content, "error": None}
            
        except Exception as e:
            logger.error(f"Error during {self.engine_name} processing: {e}", exc_info=True)
            return {"content": None, "error": str(e)}

    def _analyze_event(self, event_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes an event payload and extracts insights.
        
        Args:
            event_payload (Dict[str, Any]): The event data to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
        """
        analysis = {
            "timestamp": event_payload.get("timestamp", "unknown"),
            "event_type": event_payload.get("event_type", "general"),
            "metrics": {},
            "insights": [],
            "focus_area": self.analysis_focus
        }
        
        # Analyze based on tracked metrics
        for metric in self.metrics_tracked:
            if metric == "interaction_count":
                analysis["metrics"][metric] = len(self.state.get("analysis_results", []))
            elif metric == "response_time":
                analysis["metrics"][metric] = "immediate"  # Placeholder
            elif metric == "sentiment_score":
                analysis["metrics"][metric] = self._analyze_sentiment(event_payload)
            elif metric == "complexity_level":
                analysis["metrics"][metric] = self._analyze_complexity(event_payload)
        
        # Generate insights based on the analysis focus
        analysis["insights"] = self._generate_insights(event_payload, analysis["metrics"])
        
        return analysis

    def _analyze_sentiment(self, event_payload: Dict[str, Any]) -> str:
        """
        Analyzes sentiment of the event payload.
        
        Args:
            event_payload (Dict[str, Any]): Event data
            
        Returns:
            str: Sentiment analysis result
        """
        # Simple sentiment analysis for now
        # In Phase 2, this will use more sophisticated NLP
        prompt = event_payload.get("prompt", "")
        if any(word in prompt.lower() for word in ["good", "great", "excellent", "wonderful"]):
            return "positive"
        elif any(word in prompt.lower() for word in ["bad", "terrible", "awful", "horrible"]):
            return "negative"
        else:
            return "neutral"

    def _analyze_complexity(self, event_payload: Dict[str, Any]) -> str:
        """
        Analyzes complexity of the event payload.
        
        Args:
            event_payload (Dict[str, Any]): Event data
            
        Returns:
            str: Complexity level
        """
        # Simple complexity analysis based on payload size and structure
        payload_size = len(str(event_payload))
        nested_levels = self._count_nested_levels(event_payload)
        
        if payload_size > 500 or nested_levels > 3:
            return "high"
        elif payload_size > 200 or nested_levels > 2:
            return "medium"
        else:
            return "low"

    def _count_nested_levels(self, obj: Any, level: int = 0) -> int:
        """
        Counts the maximum nesting level in a data structure.
        
        Args:
            obj (Any): Object to analyze
            level (int): Current nesting level
            
        Returns:
            int: Maximum nesting level
        """
        if isinstance(obj, dict):
            if not obj:
                return level
            return max(self._count_nested_levels(v, level + 1) for v in obj.values())
        elif isinstance(obj, list):
            if not obj:
                return level
            return max(self._count_nested_levels(item, level + 1) for item in obj)
        else:
            return level

    def _generate_insights(self, event_payload: Dict[str, Any], metrics: Dict[str, Any]) -> List[str]:
        """
        Generates insights based on event data and metrics.
        
        Args:
            event_payload (Dict[str, Any]): Event data
            metrics (Dict[str, Any]): Calculated metrics
            
        Returns:
            List[str]: List of insights
        """
        insights = []
        
        # Generate insights based on analysis focus
        if "behavioral" in self.analysis_focus.lower():
            insights.append(f"Behavioral pattern detected with {metrics.get('sentiment_score', 'unknown')} sentiment")
        
        if "outcomes" in self.analysis_focus.lower():
            insights.append(f"Event complexity is {metrics.get('complexity_level', 'unknown')}, suggesting specific outcome patterns")
        
        # Add interaction-based insights
        interaction_count = metrics.get("interaction_count", 0)
        if interaction_count > 5:
            insights.append("High interaction frequency detected - scenario is actively engaging")
        elif interaction_count == 0:
            insights.append("First interaction - establishing baseline patterns")
        
        return insights

    def _create_analysis_prompt(self, event_payload: Dict[str, Any], analysis_result: Dict[str, Any]) -> str:
        """
        Creates an analysis prompt for the LLM.
        
        Args:
            event_payload (Dict[str, Any]): Original event data
            analysis_result (Dict[str, Any]): Analysis results
            
        Returns:
            str: Analysis prompt for LLM
        """
        prompt = f"You are an analyst focused on {self.analysis_focus}. "
        prompt += f"Analyze the following event and provide insights:\n\n"
        prompt += f"Event Type: {analysis_result.get('event_type', 'unknown')}\n"
        prompt += f"Event Data: {event_payload}\n\n"
        prompt += f"Metrics Calculated:\n"
        
        metrics = analysis_result.get("metrics", {})
        for metric, value in metrics.items():
            prompt += f"- {metric}: {value}\n"
        
        prompt += f"\nProvide analytical insights focusing on {self.analysis_focus}. "
        prompt += "Be concise and actionable in your analysis."
        
        return prompt

    def _generate_analysis_response(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generates a human-readable analysis response.
        
        Args:
            analysis_result (Dict[str, Any]): Analysis results
            
        Returns:
            str: Formatted analysis response
        """
        response = f"[Analyst - {self.analysis_focus}]: "
        response += f"Analysis of {analysis_result['event_type']} event reveals:\n"
        
        # Add metrics summary
        metrics = analysis_result.get("metrics", {})
        if metrics:
            response += "Metrics: "
            metric_strings = [f"{k}={v}" for k, v in metrics.items()]
            response += ", ".join(metric_strings) + "\n"
        
        # Add insights
        insights = analysis_result.get("insights", [])
        if insights:
            response += "Key Insights:\n"
            for i, insight in enumerate(insights, 1):
                response += f"  {i}. {insight}\n"
        
        return response.strip()

    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Returns a summary of all analyses performed.
        
        Returns:
            Dict[str, Any]: Analysis summary
        """
        results = self.state.get("analysis_results", [])
        
        return {
            "engine_name": self.engine_name,
            "analysis_focus": self.analysis_focus,
            "total_analyses": len(results),
            "metrics_tracked": self.metrics_tracked,
            "recent_insights": [r.get("insights", []) for r in results[-3:]]  # Last 3 analyses
        }

    def set_analysis_focus(self, focus: str) -> None:
        """
        Updates the analysis focus.
        
        Args:
            focus (str): New analysis focus
        """
        self.analysis_focus = focus
        self.state["analysis_focus"] = focus
        logger.info(f"Analysis focus updated to: {focus}")

    def add_metric(self, metric_name: str) -> None:
        """
        Adds a new metric to track.
        
        Args:
            metric_name (str): Name of the metric to track
        """
        if metric_name not in self.metrics_tracked:
            self.metrics_tracked.append(metric_name)
            self.state["metrics_tracked"] = self.metrics_tracked
            logger.info(f"Added metric to track: {metric_name}")
