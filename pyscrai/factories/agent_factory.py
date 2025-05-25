"""
Agent factory for creating agent instances from templates
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..databases.models import AgentTemplate, AgentInstance, ScenarioRun
from ..engines.base_engine import BaseEngine


class AgentFactory:
    """Factory for creating agent instances from templates"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_agent_instance(
        self,
        template_id: int,
        scenario_run_id: int,
        instance_name: str,
        runtime_config: Optional[Dict[str, Any]] = None
    ) -> AgentInstance:
        """Create an agent instance from a template"""
        
        # Get the template
        template = self.db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Agent template with ID {template_id} not found")
        
        # Get the scenario run
        scenario_run = self.db.query(ScenarioRun).filter(ScenarioRun.id == scenario_run_id).first()
        if not scenario_run:
            raise ValueError(f"Scenario run with ID {scenario_run_id} not found")
        
        # Create the instance
        instance = AgentInstance(
            template_id=template_id,
            scenario_run_id=scenario_run_id,
            instance_name=instance_name,
            runtime_config=runtime_config or {},
            state={}
        )
        
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        
        return instance

    def create_agent_engine(
        self,
        instance_id: int,
        engine_type: str = "base",
        storage_path: Optional[str] = None,
        model_provider: str = "openrouter"
    ) -> BaseEngine:
        """Create an engine from an agent instance"""
        
        instance = self.db.query(AgentInstance).filter(AgentInstance.id == instance_id).first()
        if not instance:
            raise ValueError(f"Agent instance with ID {instance_id} not found")
        
        # Merge template and runtime configs
        template = instance.template
        agent_config = {
            "personality_config": template.personality_config,
            "model_config": template.llm_config,  # Using llm_config instead of model_config
            "tools_config": template.tools_config,
            "runtime_config": instance.runtime_config
        }
        
        # For Phase 1, we only use the base engine
        # Specialized engines (ActorEngine, NarratorEngine, AnalystEngine) will be implemented in Phase 2
        if engine_type in ["actor", "narrator", "analyst"]:
            # Log that we're using base engine instead of specialized engine
            print(f"Warning: {engine_type} engine not yet implemented, using base engine")
        
        return BaseEngine(agent_config, storage_path, model_provider)
    
    def update_instance_state(self, instance_id: int, state_update: Dict[str, Any]) -> AgentInstance:
        """Update the state of an agent instance"""
        instance = self.db.query(AgentInstance).filter(AgentInstance.id == instance_id).first()
        if not instance:
            raise ValueError(f"Agent instance with ID {instance_id} not found")
        
        if instance.state is None:
            instance.state = {}
        
        instance.state.update(state_update)
        self.db.commit()
        self.db.refresh(instance)
        
        return instance
    
    def get_instance(self, instance_id: int) -> Optional[AgentInstance]:
        """Get an agent instance by ID"""
        return self.db.query(AgentInstance).filter(AgentInstance.id == instance_id).first()
    
    def list_instances_for_scenario(self, scenario_run_id: int) -> list[AgentInstance]:
        """List all agent instances for a scenario run"""
        return self.db.query(AgentInstance).filter(AgentInstance.scenario_run_id == scenario_run_id).all()
