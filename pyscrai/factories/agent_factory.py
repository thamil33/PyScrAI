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
        engine_type: Optional[str] = None,
        storage_path: Optional[str] = None,
        model_provider: str = "openrouter"
    ) -> BaseEngine:
        """Create an engine from an agent instance"""
        
        # If instance_id is an AgentInstance object, get its id
        if isinstance(instance_id, AgentInstance):
            instance_id = instance_id.id
        instance = self.db.query(AgentInstance).filter(AgentInstance.id == instance_id).first()
        if not instance:
            raise ValueError(f"Agent instance with ID {instance_id} not found")
        
        # Get template and determine engine type
        template = instance.template
        
        # Determine engine type from template if not explicitly provided
        if engine_type is None:
            # Check if template has engine_type field
            if hasattr(template, 'engine_type') and template.engine_type:
                engine_type = template.engine_type
            else:
                # Fall back to checking personality_config for engine_type
                engine_type = template.personality_config.get("engine_type", "base")
        
        # Merge template and runtime configs
        agent_config = {
            "personality_config": template.personality_config,
            "model_config": template.llm_config,  # Using llm_config instead of model_config
            "tools_config": template.tools_config,
            "runtime_config": instance.runtime_config
        }
        
        # Import specialized engines
        from ..engines.actor_engine import ActorEngine
        from ..engines.narrator_engine import NarratorEngine
        from ..engines.analyst_engine import AnalystEngine
        
        # Create appropriate engine based on type
        if engine_type.lower() == "actor":
            # Extract character-specific config from template
            personality = template.personality_config
            character_name = personality.get("role", "Character")
            personality_traits = personality.get("backstory", "A character in the scenario")
            
            return ActorEngine(
                agent_config=agent_config,
                character_name=character_name,
                personality_traits=personality_traits,
                storage_path=storage_path,
                model_provider=model_provider
            )
            
        elif engine_type.lower() == "narrator":
            # Extract narrator-specific config from template
            personality = template.personality_config
            traits = personality.get("traits", {})
            narrative_style = "descriptive and engaging"
            perspective = "third_person"
            
            # Override with template values if available
            if isinstance(traits, dict):
                if "narrative_style" in traits:
                    narrative_style = traits["narrative_style"]
                if "perspective" in traits:
                    perspective = traits["perspective"]
            
            return NarratorEngine(
                agent_config=agent_config,
                narrative_style=narrative_style,
                perspective=perspective,
                storage_path=storage_path,
                model_provider=model_provider
            )
            
        elif engine_type.lower() == "analyst":
            # Extract analyst-specific config from template
            personality = template.personality_config
            analysis_focus = personality.get("backstory", "behavioral patterns and outcomes")
            
            return AnalystEngine(
                agent_config=agent_config,
                analysis_focus=analysis_focus,
                storage_path=storage_path,
                model_provider=model_provider
            )
            
        else:
            # Default to base engine
            return BaseEngine(agent_config, storage_path, model_provider)
    
    def update_instance_state(self, instance_id: int, state_update: Dict[str, Any]) -> AgentInstance:
        """Update the state of an agent instance"""
        # If instance_id is an AgentInstance object, get its id
        if isinstance(instance_id, AgentInstance):
            instance_id = instance_id.id
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
        # If instance_id is an AgentInstance object, get its id
        if isinstance(instance_id, AgentInstance):
            instance_id = instance_id.id
        return self.db.query(AgentInstance).filter(AgentInstance.id == instance_id).first()
    
    def list_instances_for_scenario(self, scenario_run_id: int) -> list[AgentInstance]:
        """List all agent instances for a scenario run"""
        return self.db.query(AgentInstance).filter(AgentInstance.scenario_run_id == scenario_run_id).all()
