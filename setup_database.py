"""
Database initialization and sample data loading for PyScrAI
"""

import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import pyscrai modules
sys.path.append(str(Path(__file__).parent.parent))

from pyscrai.databases import init_database, get_db_session
from pyscrai.databases.models.schemas import AgentTemplateCreate, ScenarioTemplateCreate
from pyscrai.factories.template_manager import TemplateManager
from pyscrai.utils.config import Config
from alembic.config import Config as AlembicConfig
from alembic import command


def load_agent_template_from_file(file_path: Path) -> AgentTemplateCreate:
    """Load an agent template from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return AgentTemplateCreate(**data)


def load_scenario_template_from_file(file_path: Path) -> ScenarioTemplateCreate:
    """Load a scenario template from JSON file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    return ScenarioTemplateCreate(**data)


def setup_database():
    """Initialize database and load sample templates"""
    print("Setting up PyScrAI database...")
    
    # Ensure directories exist
    Config.ensure_directories()
    
    # Initialize database
    print("Initializing database schema...")
    # init_database() # This will be handled by Alembic migrations
    # print("✓ Database schema created")

    # Apply Alembic migrations
    print("Applying database migrations...")
    alembic_cfg = AlembicConfig(str(Path(__file__).parent / "pyscrai" / "databases" / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(Path(__file__).parent / "pyscrai" / "databases" / "alembic"))
    # Construct the correct path to the database file for sqlalchemy.url
    db_path = Config.DATA_DIR / 'pyscrai.db'
    alembic_cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path.resolve()}")
    command.upgrade(alembic_cfg, "head")
    print("✓ Database migrations applied")
    
    # Load sample templates
    db = get_db_session()
    try:
        manager = TemplateManager(db)
        
        # Load agent templates
        agent_templates_dir = Config.TEMPLATES_DIR / "agents"
        agent_templates_loaded = 0
        
        for template_file in agent_templates_dir.glob("*.json"):
            try:
                template_data = load_agent_template_from_file(template_file)
                
                # Check if template already exists
                existing = manager.get_agent_template_by_name(template_data.name)
                if existing:
                    print(f"  - Agent template '{template_data.name}' already exists, skipping")
                    continue
                
                template = manager.create_agent_template(template_data)
                print(f"  ✓ Loaded agent template: {template.name} (ID: {template.id})")
                agent_templates_loaded += 1
            except Exception as e:
                print(f"  ✗ Failed to load {template_file.name}: {e}")
        
        print(f"✓ Loaded {agent_templates_loaded} agent templates")
        
        # Load scenario templates  
        scenario_templates_dir = Config.TEMPLATES_DIR / "scenarios"
        scenario_templates_loaded = 0
        
        for template_file in scenario_templates_dir.glob("*.json"):
            try:
                template_data = load_scenario_template_from_file(template_file)
                
                # Check if template already exists
                existing = manager.get_scenario_template_by_name(template_data.name)
                if existing:
                    print(f"  - Scenario template '{template_data.name}' already exists, skipping")
                    continue
                
                template = manager.create_scenario_template(template_data)
                print(f"  ✓ Loaded scenario template: {template.name} (ID: {template.id})")
                scenario_templates_loaded += 1
            except Exception as e:
                print(f"  ✗ Failed to load {template_file.name}: {e}")
        
        print(f"✓ Loaded {scenario_templates_loaded} scenario templates")
        
        # Summary
        print(f"\n🎉 Database setup complete!")
        print(f"   Database location: {Config.DATA_DIR / 'pyscrai.db'}")
        print(f"   Agent templates: {agent_templates_loaded} loaded")
        print(f"   Scenario templates: {scenario_templates_loaded} loaded")
        
    finally:
        db.close()


def list_templates():
    """List all loaded templates"""
    db = get_db_session()
    try:
        manager = TemplateManager(db)
        
        print("\n📝 Available Agent Templates:")
        agent_templates = manager.list_agent_templates()
        for template in agent_templates:
            print(f"  - {template.name} (ID: {template.id})")
            print(f"    Description: {template.description}")
        
        print("\n🎬 Available Scenario Templates:")
        scenario_templates = manager.list_scenario_templates()
        for template in scenario_templates:
            print(f"  - {template.name} (ID: {template.id})")
            print(f"    Description: {template.description}")
            
        if not agent_templates and not scenario_templates:
            print("  No templates found. Run setup first.")
            
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="PyScrAI Database Setup")
    parser.add_argument("--setup", action="store_true", help="Initialize database and load templates")
    parser.add_argument("--list", action="store_true", help="List available templates")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_database()
    elif args.list:
        list_templates()
    else:
        # Default: run setup
        setup_database()
