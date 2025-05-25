"""
Template manager for CRUD operations on agent and scenario templates
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..databases.models import (
    AgentTemplate, 
    ScenarioTemplate
)
from ..databases.models.schemas import (
    AgentTemplateCreate, 
    ScenarioTemplateCreate,
    AgentTemplateUpdate,
    ScenarioTemplateUpdate
)
import json
from pathlib import Path


class TemplateManager:
    """Manages agent and scenario templates with CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Agent Template Methods
    def create_agent_template(self, template_data: AgentTemplateCreate) -> AgentTemplate:
        """Create a new agent template"""
        db_template = AgentTemplate(**template_data.dict())
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template
    
    def get_agent_template(self, template_id: int) -> Optional[AgentTemplate]:
        """Get agent template by ID"""
        return self.db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()
    
    def get_agent_template_by_name(self, name: str) -> Optional[AgentTemplate]:
        """Get agent template by name"""
        return self.db.query(AgentTemplate).filter(AgentTemplate.name == name).first()
    
    def list_agent_templates(self) -> List[AgentTemplate]:
        """List all agent templates"""
        return self.db.query(AgentTemplate).all()
    
    def update_agent_template(self, template_id: int, update_data: AgentTemplateUpdate) -> Optional[AgentTemplate]:
        """Update an agent template"""
        template = self.get_agent_template(template_id)
        if not template:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete_agent_template(self, template_id: int) -> bool:
        """Delete an agent template"""
        template = self.get_agent_template(template_id)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True
    
    # Scenario Template Methods
    def create_scenario_template(self, template_data: ScenarioTemplateCreate) -> ScenarioTemplate:
        """Create a new scenario template"""
        db_template = ScenarioTemplate(**template_data.dict())
        self.db.add(db_template)
        self.db.commit()
        self.db.refresh(db_template)
        return db_template
    
    def get_scenario_template(self, template_id: int) -> Optional[ScenarioTemplate]:
        """Get scenario template by ID"""
        return self.db.query(ScenarioTemplate).filter(ScenarioTemplate.id == template_id).first()
    
    def get_scenario_template_by_name(self, name: str) -> Optional[ScenarioTemplate]:
        """Get scenario template by name"""
        return self.db.query(ScenarioTemplate).filter(ScenarioTemplate.name == name).first()
    
    def list_scenario_templates(self) -> List[ScenarioTemplate]:
        """List all scenario templates"""
        return self.db.query(ScenarioTemplate).all()
    
    def update_scenario_template(self, template_id: int, update_data: ScenarioTemplateUpdate) -> Optional[ScenarioTemplate]:
        """Update a scenario template"""
        template = self.get_scenario_template(template_id)
        if not template:
            return None
        
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete_scenario_template(self, template_id: int) -> bool:
        """Delete a scenario template"""
        template = self.get_scenario_template(template_id)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True
    
    # Template Import/Export
    def export_agent_template_to_file(self, template_id: int, file_path: Path):
        """Export an agent template to JSON file"""
        template = self.get_agent_template(template_id)
        if not template:
            raise ValueError("Agent template not found")
        
        template_dict = {
            "name": template.name,
            "description": template.description,
            "personality_config": template.personality_config,
            "model_config": template.model_config,
            "tools_config": template.tools_config,
        }
        
        with open(file_path, 'w') as f:
            json.dump(template_dict, f, indent=2)
    
    def export_scenario_template_to_file(self, template_id: int, file_path: Path):
        """Export a scenario template to JSON file"""
        template = self.get_scenario_template(template_id)
        if not template:
            raise ValueError("Scenario template not found")
        
        template_dict = {
            "name": template.name,
            "description": template.description,
            "config": template.config,
            "agent_roles": template.agent_roles,
            "event_flow": template.event_flow,
        }
        
        with open(file_path, 'w') as f:
            json.dump(template_dict, f, indent=2)
    
    def import_agent_template_from_file(self, file_path: Path) -> AgentTemplate:
        """Import an agent template from JSON file"""
        with open(file_path, 'r') as f:
            template_data = json.load(f)
        
        template_create = AgentTemplateCreate(**template_data)
        return self.create_agent_template(template_create)
    
    def import_scenario_template_from_file(self, file_path: Path) -> ScenarioTemplate:
        """Import a scenario template from JSON file"""
        with open(file_path, 'r') as f:
            template_data = json.load(f)
        
        template_create = ScenarioTemplateCreate(**template_data)
        return self.create_scenario_template(template_create)
