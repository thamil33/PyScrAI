"""
Scenario factory for creating scenario runs from templates
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime
from pyscrai.databases.models import ScenarioTemplate, ScenarioRun, AgentInstance
from pyscrai.factories.agent_factory import AgentFactory
from pyscrai.factories.template_manager import TemplateManager


class ScenarioFactory:
    """Factory for creating scenario runs from templates"""
    
    def __init__(self, db: Session):
        self.db = db
        self.agent_factory = AgentFactory(db)
        self.template_manager = TemplateManager(db)  # Add template_manager attribute
    
    def create_scenario_run(
        self,
        template_id: int,
        run_name: str,
        runtime_config: Optional[Dict[str, Any]] = None
    ) -> ScenarioRun:
        """Create a scenario run from a template"""
        
        # Get the template
        template = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
        if not template:
            raise ValueError(f"Scenario template with ID {template_id} not found")
        
        # Create the scenario run
        scenario_run = ScenarioRun(
            template_id=template_id,
            name=run_name,
            status="pending",
            config=runtime_config or {},
            results={},
            created_at=datetime.utcnow()
        )
        
        self.db.add(scenario_run)
        self.db.commit()
        self.db.refresh(scenario_run)
        
        return scenario_run
    
    def setup_agents_for_scenario(
        self,
        scenario_run_id: int,
        agent_overrides: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[AgentInstance]:
        """Set up all required agents for a scenario run"""
        
        scenario_run = self.db.query(ScenarioRun).filter(ScenarioRun.id == scenario_run_id).first()
        if not scenario_run:
            raise ValueError(f"Scenario run with ID {scenario_run_id} not found")
        
        template = scenario_run.template
        agent_roles = template.agent_roles
        agent_overrides = agent_overrides or {}
        
        created_instances = []
        
        for role_name, role_config in agent_roles.items():
            template_name = role_config.get("template_name")
            if not template_name:
                continue
            
            # Find the agent template by name
            from ..databases.models import AgentTemplate
            agent_template = self.db.query(AgentTemplate).filter(AgentTemplate.name == template_name).first()
            if not agent_template:
                raise ValueError(f"Agent template '{template_name}' not found for role '{role_name}'")
            
            # Get any overrides for this role
            role_overrides = agent_overrides.get(role_name, {})
            
            # Create instance name
            instance_name = f"{role_name}_{scenario_run.name}"
            
            # Create the agent instance
            instance = self.agent_factory.create_agent_instance(
                template_id=agent_template.id,
                scenario_run_id=scenario_run_id,
                instance_name=instance_name,
                runtime_config=role_overrides
            )
            
            created_instances.append(instance)
        
        return created_instances
    
    def start_scenario_run(self, scenario_run_id: int) -> ScenarioRun:
        """Start a scenario run"""
        scenario_run = self.db.query(ScenarioRun).filter(ScenarioRun.id == scenario_run_id).first()
        if not scenario_run:
            raise ValueError(f"Scenario run with ID {scenario_run_id} not found")
        
        scenario_run.status = "running"
        scenario_run.started_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(scenario_run)
        
        return scenario_run
    
    def complete_scenario_run(
        self, 
        scenario_run_id: int, 
        results: Dict[str, Any],
        status: str = "completed"
    ) -> ScenarioRun:
        """Complete a scenario run with results"""
        scenario_run = self.db.query(ScenarioRun).filter(ScenarioRun.id == scenario_run_id).first()
        if not scenario_run:
            raise ValueError(f"Scenario run with ID {scenario_run_id} not found")
        
        scenario_run.status = status
        scenario_run.completed_at = datetime.utcnow()
        scenario_run.results = results
        
        self.db.commit()
        self.db.refresh(scenario_run)
        
        return scenario_run
    
    def get_scenario_run(self, scenario_run_id: int) -> Optional[ScenarioRun]:
        """Get a scenario run by ID"""
        return self.db.query(ScenarioRun).filter(ScenarioRun.id == scenario_run_id).first()
    
    def list_scenario_runs(self, template_id: Optional[int] = None) -> List[ScenarioRun]:
        """List scenario runs, optionally filtered by template"""
        query = self.db.query(ScenarioRun)
        if template_id:
            query = query.filter(ScenarioRun.template_id == template_id)
        return query.all()
    
    def create_scenario_run_from_template(
        self,
        template_name: str,
        run_name: str,
        agent_configs: Optional[List[Dict[str, Any]]] = None,
        runtime_config: Optional[Dict[str, Any]] = None
    ) -> ScenarioRun:
        """Create a scenario run from a template name with agent configurations"""
        
        # Find the scenario template by name
        template = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.name == template_name).first()
        if not template:
            raise ValueError(f"Scenario template '{template_name}' not found")
        
        # Create the scenario run
        scenario_run = self.create_scenario_run(
            template_id=template.id,
            run_name=run_name,
            runtime_config=runtime_config or {}
        )
        
        # Setup agent instances based on provided configurations or template defaults
        if agent_configs:
            self._setup_agents_from_configs(scenario_run.id, agent_configs)
        elif template.agent_roles:
            self.setup_agents_for_scenario(scenario_run_id=scenario_run.id)
        
        return scenario_run
    
    def _setup_agents_from_configs(
        self,
        scenario_run_id: int,
        agent_configs: List[Dict[str, Any]]
    ) -> List[AgentInstance]:
        """Set up agents from explicit configurations"""
        
        created_instances = []
        
        for config in agent_configs:
            template_name = config.get("template_name")
            instance_name = config.get("instance_name")
            runtime_config = config.get("runtime_config", {})
            
            if not template_name or not instance_name:
                raise ValueError("Each agent config must have 'template_name' and 'instance_name'")
            
            # Find the agent template by name
            from ..databases.models import AgentTemplate
            agent_template = self.db.query(AgentTemplate).filter(AgentTemplate.name == template_name).first()
            if not agent_template:
                raise ValueError(f"Agent template '{template_name}' not found")
            
            # Create the agent instance
            instance = self.agent_factory.create_agent_instance(
                template_id=agent_template.id,
                scenario_run_id=scenario_run_id,
                instance_name=instance_name,
                runtime_config=runtime_config
            )
            
            created_instances.append(instance)
        
        return created_instances

    def create_scenario_from_template(
        self,
        template_id: int,
        name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ScenarioRun:
        """Create a complete scenario from a template, including agent instances"""
        # First create the scenario run
        scenario_run = self.create_scenario_run(
            template_id=template_id,
            run_name=name,
            runtime_config=config or {}
        )
        
        # Get template details
        template = self.db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
        
        # Setup agent instances based on template roles
        if template and template.agent_roles:
            self.setup_agents_for_scenario(
                scenario_run_id=scenario_run.id
            )
        
        return scenario_run
