"""
Template manager for CRUD operations on agent and scenario templates
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import json
from pathlib import Path

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
from ..databases.models.template_validators import (
    AgentTemplateValidator,
    ScenarioTemplateValidator
)


class TemplateManager:
    """Manages agent and scenario templates with CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db

    def _validate_agent_template(self, template_data: dict) -> None:
        """Validate agent template data against the enhanced schema"""
        try:
            AgentTemplateValidator(**template_data)
        except Exception as e:
            raise ValueError(f"Invalid agent template: {str(e)}")

    def _validate_scenario_template(self, template_data: dict) -> None:
        """Validate scenario template data against the enhanced schema"""
        try:
            ScenarioTemplateValidator(**template_data)
        except Exception as e:
            raise ValueError(f"Invalid scenario template: {str(e)}")

    # Agent Template Methods
    def create_agent_template(self, template_data: AgentTemplateCreate) -> AgentTemplate:
        """Create a new agent template
        
        Args:
            template_data: The AgentTemplateCreate object containing template data
            
        Returns:
            The created AgentTemplate
            
        Raises:
            ValueError: If template data is invalid
        """
        try:
            self._validate_agent_template(template_data.dict())
            db_template = AgentTemplate(**template_data.dict())
            self.db.add(db_template)
            self.db.commit()
            self.db.refresh(db_template)
            return db_template
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create template: {str(e)}")
    
    def get_agent_template(self, template_id: int) -> Optional[AgentTemplate]:
        """Get agent template by ID
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            The AgentTemplate if found, None otherwise
        """
        return self.db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()
    
    def get_agent_template_by_name(self, name: str) -> Optional[AgentTemplate]:
        """Get agent template by name
        
        Args:
            name: The name of the template to retrieve
            
        Returns:
            The AgentTemplate if found, None otherwise
        """
        return self.db.query(AgentTemplate).filter(AgentTemplate.name == name).first()
    
    def list_agent_templates(self) -> List[AgentTemplate]:
        """List all agent templates
        
        Returns:
            List of all AgentTemplate objects in the database
        """
        return self.db.query(AgentTemplate).all()
    
    def update_agent_template(self, template_id: int, update_data: AgentTemplateUpdate) -> Optional[AgentTemplate]:
        """Update an agent template
        
        Args:
            template_id: The ID of the template to update
            update_data: The AgentTemplateUpdate object containing fields to update
            
        Returns:
            The updated AgentTemplate or None if template not found
            
        Raises:
            ValueError: If the update data is invalid
        """
        template = self.get_agent_template(template_id)
        if not template:
            return None
        
        # Create a merged dict of existing and update data for validation
        merged_data = template.__dict__.copy()
        update_dict = update_data.dict(exclude_unset=True)
        merged_data.update(update_dict)
        
        # Validate the merged data
        try:
            self._validate_agent_template(merged_data)
        except ValueError as e:
            self.db.rollback()
            raise ValueError(f"Invalid update data: {str(e)}")
        
        # Apply updates
        for key, value in update_dict.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(template)
            return template
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update template: {str(e)}")
    
    def delete_agent_template(self, template_id: int) -> bool:
        """Delete an agent template
        
        Args:
            template_id: The ID of the template to delete
            
        Returns:
            True if template was deleted, False if template not found
            
        Raises:
            ValueError: If deletion fails
        """
        template = self.get_agent_template(template_id)
        if not template:
            return False
        
        try:
            self.db.delete(template)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to delete template: {str(e)}")
    
    # Scenario Template Methods
    def create_scenario_template(self, template_data: ScenarioTemplateCreate) -> ScenarioTemplate:
        """Create a new scenario template
        
        Args:
            template_data: The ScenarioTemplateCreate object containing template data
            
        Returns:
            The created ScenarioTemplate
            
        Raises:
            ValueError: If template data is invalid
        """
        try:
            self._validate_scenario_template(template_data.dict())
            db_template = ScenarioTemplate(**template_data.dict())
            self.db.add(db_template)
            self.db.commit()
            self.db.refresh(db_template)
            return db_template
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to create template: {str(e)}")
    
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
        """Update a scenario template
        
        Args:
            template_id: The ID of the template to update
            update_data: The ScenarioTemplateUpdate object containing fields to update
            
        Returns:
            The updated ScenarioTemplate or None if template not found
            
        Raises:
            ValueError: If the update data is invalid
        """
        template = self.get_scenario_template(template_id)
        if not template:
            return None
        
        # Create a merged dict of existing and update data for validation
        merged_data = template.__dict__.copy()
        update_dict = update_data.dict(exclude_unset=True)
        merged_data.update(update_dict)
        
        # Validate the merged data
        try:
            self._validate_scenario_template(merged_data)
        except ValueError as e:
            self.db.rollback()
            raise ValueError(f"Invalid update data: {str(e)}")
        
        # Apply updates
        for key, value in update_dict.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        try:
            self.db.commit()
            self.db.refresh(template)
            return template
        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Failed to update template: {str(e)}")
    
    def delete_scenario_template(self, template_id: int) -> bool:
        """Delete a scenario template"""
        template = self.get_scenario_template(template_id)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True
    
    # Template Import/Export
    def export_agent_template_to_file(self, template_id: int, file_path: Path) -> None:
        """Export an agent template to JSON file
        
        Args:
            template_id: The ID of the template to export
            file_path: Path where the JSON file will be saved
            
        Raises:
            ValueError: If template not found or export fails
            IOError: If file operations fail
        """
        template = self.get_agent_template(template_id)
        if not template:
            raise ValueError(f"Agent template with ID {template_id} not found")
        
        template_dict = {
            "name": template.name,
            "description": template.description,
            "personality_config": template.personality_config,
            "llm_config": template.llm_config,  # Fixed: was model_config
            "tools_config": template.tools_config,
        }
        
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(template_dict, f, indent=2)
        except Exception as e:
            raise IOError(f"Failed to export template: {str(e)}")
    
    def export_scenario_template_to_file(self, template_id: int, file_path: Path) -> None:
        """Export a scenario template to JSON file
        
        Args:
            template_id: The ID of the template to export
            file_path: Path where the JSON file will be saved
            
        Raises:
            ValueError: If template not found or export fails
            IOError: If file operations fail
        """
        template = self.get_scenario_template(template_id)
        if not template:
            raise ValueError(f"Scenario template with ID {template_id} not found")
        
        template_dict = {
            "name": template.name,
            "description": template.description,
            "config": template.config,
            "agent_roles": template.agent_roles,
            "event_flow": template.event_flow,
        }
        
        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                json.dump(template_dict, f, indent=2)
        except Exception as e:
            raise IOError(f"Failed to export template: {str(e)}")
    
    def import_agent_template_from_file(self, file_path: Path) -> AgentTemplate:
        """Import an agent template from JSON file
        
        Args:
            file_path: Path to the JSON file containing the template
            
        Returns:
            The imported AgentTemplate
            
        Raises:
            ValueError: If template data is invalid
            IOError: If file operations fail
        """
        try:
            with open(file_path, 'r') as f:
                template_data = json.load(f)
        except Exception as e:
            raise IOError(f"Failed to read template file: {str(e)}")
        
        try:
            # Validate data before creating
            self._validate_agent_template(template_data)
            
            template_create = AgentTemplateCreate(**template_data)
            return self.create_agent_template(template_create)
        except Exception as e:
            raise ValueError(f"Invalid template data: {str(e)}")
    
    def import_scenario_template_from_file(self, file_path: Path) -> ScenarioTemplate:
        """Import a scenario template from JSON file
        
        Args:
            file_path: Path to the JSON file containing the template
            
        Returns:
            The imported ScenarioTemplate
            
        Raises:
            ValueError: If template data is invalid
            IOError: If file operations fail
        """
        try:
            with open(file_path, 'r') as f:
                template_data = json.load(f)
        except Exception as e:
            raise IOError(f"Failed to read template file: {str(e)}")
        
        try:
            # Validate data before creating
            self._validate_scenario_template(template_data)
            
            template_create = ScenarioTemplateCreate(**template_data)
            return self.create_scenario_template(template_create)
        except Exception as e:
            raise ValueError(f"Invalid template data: {str(e)}")
