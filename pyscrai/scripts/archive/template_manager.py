#!/usr/bin/env python
"""
Template management utility for PyScrAI

This script provides utilities for managing PyScrAI templates:
1. Listing templates in the database
2. Exporting templates from the database to files
3. Verifying templates against their validators
4. (Placeholder) Migration utilities for older template formats
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from colorama import init, Fore, Style

# Add the project root to the path to enable imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Initialize colorama for cross-platform colored output
init()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define template directories
TEMPLATES_ROOT = project_root / "pyscrai" / "templates"
AGENT_TEMPLATES_DIR = TEMPLATES_ROOT / "agents"
SCENARIO_TEMPLATES_DIR = TEMPLATES_ROOT / "scenarios"
EVENTS_DIR = TEMPLATES_ROOT / "events"

# Define colorful output helpers
def print_header(text: str) -> None:
    """Print a colorful header"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{text}{Style.RESET_ALL}")

def print_success(text: str) -> None:
    """Print a success message"""
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text: str) -> None:
    """Print an error message"""
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_warning(text: str) -> None:
    """Print a warning message"""
    print(f"{Fore.YELLOW}⚠ {text}{Style.RESET_ALL}")

def print_info(text: str) -> None:
    """Print an info message"""
    print(f"{Fore.BLUE}ℹ {text}{Style.RESET_ALL}")

def print_template_info(template_type: str, template_id: int, name: str, description: str) -> None:
    """Print template information in a formatted way"""
    print(f"{Fore.MAGENTA}[{template_type}]{Style.RESET_ALL} {Fore.WHITE}ID: {template_id} | {Fore.YELLOW}{name}{Style.RESET_ALL}")
    if description:
        print(f"   {description}")

def list_templates() -> None:
    """
    List all templates in the database with their ID, name, and description
    """
    try:
        from pyscrai.databases.database import get_db_session
        from pyscrai.databases.models import AgentTemplate, ScenarioTemplate
        
        db = get_db_session()
        try:
            # Get all agent templates
            agent_templates = db.query(AgentTemplate).all()
            
            # Get all scenario templates
            scenario_templates = db.query(ScenarioTemplate).all()
            
            # Print results
            print_header("Agent Templates")
            if agent_templates:
                for template in agent_templates:
                    print_template_info("Agent", template.id, template.name, template.description)
            else:
                print_info("No agent templates found in database.")
                
            print_header("Scenario Templates")
            if scenario_templates:
                for template in scenario_templates:
                    print_template_info("Scenario", template.id, template.name, template.description)
            else:
                print_info("No scenario templates found in database.")
                
            # Print summary
            print_header("Summary")
            print(f"Total templates: {len(agent_templates) + len(scenario_templates)}")
            print(f"Agent templates: {len(agent_templates)}")
            print(f"Scenario templates: {len(scenario_templates)}")
            
        finally:
            db.close()
    
    except Exception as e:
        print_error(f"Failed to list templates: {e}")
        logger.error(f"Error listing templates: {e}", exc_info=True)
        return False
        
    return True

def export_template(template_type: str, template_id: int, output_dir: Optional[str] = None) -> bool:
    """
    Export a specific template to a JSON file
    
    Args:
        template_type: Either 'agent' or 'scenario'
        template_id: The ID of the template to export
        output_dir: Optional directory to save the template file to
    
    Returns:
        bool: True if export was successful, False otherwise
    """
    try:
        from pyscrai.factories.template_manager import TemplateManager
        from pyscrai.databases.database import get_db_session
        
        if template_type.lower() not in ['agent', 'scenario']:
            print_error(f"Invalid template type: {template_type}. Must be 'agent' or 'scenario'.")
            return False
        
        # Determine output directory
        if output_dir:
            output_path = Path(output_dir)
        else:
            if template_type.lower() == 'agent':
                output_path = AGENT_TEMPLATES_DIR
            else:
                output_path = SCENARIO_TEMPLATES_DIR
                
        # Ensure output directory exists
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export template
        db = get_db_session()
        try:
            template_manager = TemplateManager(db)
            
            # Get template name for filename
            if template_type.lower() == 'agent':
                template = template_manager.get_agent_template(template_id)
            else:
                template = template_manager.get_scenario_template(template_id)
                
            if not template:
                print_error(f"{template_type.capitalize()} template with ID {template_id} not found.")
                return False
                
            # Create filename from template name
            template_name = template.name
            safe_filename = "".join([c if c.isalnum() else "_" for c in template_name]).rstrip("_")
            file_path = output_path / f"{safe_filename}.json"
            
            # Export template
            if template_type.lower() == 'agent':
                template_manager.export_agent_template_to_file(template_id, file_path)
            else:
                template_manager.export_scenario_template_to_file(template_id, file_path)
                
            print_success(f"Exported {template_type} template '{template.name}' to {file_path}")
            return True
            
        finally:
            db.close()
    
    except Exception as e:
        print_error(f"Failed to export template: {e}")
        logger.error(f"Error exporting template: {e}", exc_info=True)
        return False

def export_all_templates(output_dir: Optional[str] = None) -> bool:
    """
    Export all templates from the database to JSON files
    
    Args:
        output_dir: Optional base directory to save the template files to
    
    Returns:
        bool: True if all exports were successful, False otherwise
    """
    try:
        from pyscrai.databases.database import get_db_session
        from pyscrai.databases.models import AgentTemplate, ScenarioTemplate
        
        db = get_db_session()
        try:
            # Get all agent templates
            agent_templates = db.query(AgentTemplate).all()
            
            # Get all scenario templates
            scenario_templates = db.query(ScenarioTemplate).all()
            
            # Export all agent templates
            print_header("Exporting Agent Templates")
            success_count = 0
            for template in agent_templates:
                if export_template('agent', template.id, output_dir):
                    success_count += 1
                
            # Export all scenario templates
            print_header("Exporting Scenario Templates")
            for template in scenario_templates:
                if export_template('scenario', template.id, output_dir):
                    success_count += 1
                
            # Print summary
            print_header("Export Summary")
            total_templates = len(agent_templates) + len(scenario_templates)
            print(f"Successfully exported {success_count} of {total_templates} templates")
            
            return success_count == total_templates
            
        finally:
            db.close()
    
    except Exception as e:
        print_error(f"Failed to export templates: {e}")
        logger.error(f"Error exporting templates: {e}", exc_info=True)
        return False

def verify_template_file(file_path: Union[str, Path]) -> bool:
    """
    Verify that a template file is valid against its validator
    
    Args:
        file_path: Path to the template file to verify
    
    Returns:
        bool: True if template is valid, False otherwise
    """
    try:
        from pyscrai.databases.models.template_validators import AgentTemplateValidator, ScenarioTemplateValidator
        
        file_path = Path(file_path)
        if not file_path.exists() or not file_path.is_file():
            print_error(f"Template file not found: {file_path}")
            return False
            
        # Load template data
        with open(file_path, 'r') as f:
            template_data = json.load(f)
            
        # Determine template type and validate
        if "engine_type" in template_data:
            # This is an agent template
            print_info(f"Validating agent template: {file_path.name}")
            AgentTemplateValidator(**template_data)
            print_success(f"Agent template is valid: {file_path.name}")
            return True
        elif "agent_roles" in template_data:
            # This is a scenario template
            print_info(f"Validating scenario template: {file_path.name}")
            ScenarioTemplateValidator(**template_data)
            print_success(f"Scenario template is valid: {file_path.name}")
            return True
        else:
            print_error(f"Unknown template type in file: {file_path}")
            return False
    
    except Exception as e:
        print_error(f"Template validation failed: {e}")
        logger.error(f"Error validating template: {e}", exc_info=True)
        return False

def verify_directory_templates(directory: Union[str, Path]) -> Dict[str, int]:
    """
    Verify all templates in a directory
    
    Args:
        directory: Path to directory containing templates
    
    Returns:
        Dict[str, int]: Count of valid and invalid templates
    """
    try:
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            print_error(f"Directory not found: {directory}")
            return {"valid": 0, "invalid": 0, "total": 0}
            
        # Get all JSON files
        json_files = list(directory.glob("*.json"))
        
        if not json_files:
            print_warning(f"No JSON files found in directory: {directory}")
            return {"valid": 0, "invalid": 0, "total": 0}
            
        # Verify each template
        valid_count = 0
        invalid_count = 0
        
        for file_path in json_files:
            try:
                if verify_template_file(file_path):
                    valid_count += 1
                else:
                    invalid_count += 1
            except Exception as e:
                print_error(f"Error validating {file_path.name}: {e}")
                invalid_count += 1
        
        total = valid_count + invalid_count
        
        # Print summary
        print_header("Validation Summary")
        print(f"Total templates: {total}")
        print(f"Valid templates: {valid_count}")
        print(f"Invalid templates: {invalid_count}")
        
        return {"valid": valid_count, "invalid": invalid_count, "total": total}
    
    except Exception as e:
        print_error(f"Failed to verify templates: {e}")
        logger.error(f"Error verifying templates: {e}", exc_info=True)
        return {"valid": 0, "invalid": 0, "total": 0}

def migrate_template_placeholder() -> None:
    """
    Placeholder for template migration functionality
    """
    print_header("Template Migration")
    print_info("Template migration functionality is not yet implemented.")
    print_info("This feature will allow migration from older template formats to the current format.")
    print_info("Currently, there are no older template formats that require migration.")

def print_help() -> None:
    """Print detailed help information"""
    print_header("PyScrAI Template Management Utility")
    print("""
This script provides utilities for managing PyScrAI templates:

Commands:
  list                     List all templates in the database
  export <type> <id> [dir] Export a specific template to a file
                           <type>: 'agent' or 'scenario'
                           <id>: Template ID number
                           [dir]: Optional output directory (default: pyscrai/templates/<type>s)
  export-all [dir]         Export all templates to files
                           [dir]: Optional base output directory
  verify <file>            Verify a single template file against its validator
  verify-dir <dir>         Verify all templates in a directory
  migrate                  (Placeholder) Migration utilities for older template formats
  help                     Show this help message
    """)

def main():
    """Main entry point for command line interface"""
    parser = argparse.ArgumentParser(
        description="PyScrAI Template Management Utility", 
        add_help=False
    )
    parser.add_argument('command', nargs='?', default='help')
    parser.add_argument('args', nargs='*')
    
    args = parser.parse_args()
    
    # Process commands
    if args.command == 'list':
        list_templates()
    
    elif args.command == 'export':
        if len(args.args) < 2:
            print_error("Missing required arguments for export command.")
            print("Usage: export <type> <id> [dir]")
            return 1
            
        template_type = args.args[0]
        try:
            template_id = int(args.args[1])
        except ValueError:
            print_error(f"Invalid template ID: {args.args[1]}")
            return 1
            
        output_dir = args.args[2] if len(args.args) > 2 else None
        export_template(template_type, template_id, output_dir)
    
    elif args.command == 'export-all':
        output_dir = args.args[0] if args.args else None
        export_all_templates(output_dir)
    
    elif args.command == 'verify':
        if not args.args:
            print_error("Missing required file path for verify command.")
            print("Usage: verify <file>")
            return 1
            
        verify_template_file(args.args[0])
    
    elif args.command == 'verify-dir':
        if not args.args:
            print_error("Missing required directory path for verify-dir command.")
            print("Usage: verify-dir <dir>")
            return 1
            
        verify_directory_templates(args.args[0])
    
    elif args.command == 'migrate':
        migrate_template_placeholder()
    
    elif args.command == 'help' or args.command == '-h' or args.command == '--help':
        print_help()
    
    else:
        print_error(f"Unknown command: {args.command}")
        print_help()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
