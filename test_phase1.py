"""
Test script for Phase 1 PyScrAI implementation
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import pyscrai modules
sys.path.append(str(Path(__file__).parent))

from pyscrai.databases import get_db_session
from pyscrai.factories import TemplateManager, AgentFactory, ScenarioFactory
from pyscrai.engines.base_engine import BaseEngine
from pyscrai.utils.config import Config


class TestEngine(BaseEngine):
    """Simple test engine implementation"""
    
    def _setup_tools(self):
        """No tools for basic testing"""
        return []
    
    async def process(self, input_data):
        """Simple processing for testing"""
        message = input_data.get("message", "Hello, who are you?")
        response = await self.run(message)
        return response


async def test_phase_1():
    """Test Phase 1 implementation"""
    print("🧪 Testing PyScrAI Phase 1 Implementation\n")
    
    # Test 1: Database and Template Management
    print("1️⃣ Testing Database and Template Management...")
    db = get_db_session()
    try:
        manager = TemplateManager(db)
        
        # List available templates
        agent_templates = manager.list_agent_templates()
        scenario_templates = manager.list_scenario_templates()
        
        print(f"   Found {len(agent_templates)} agent templates")
        print(f"   Found {len(scenario_templates)} scenario templates")
        
        if agent_templates:
            pope_template = next((t for t in agent_templates if "Pope" in t.name), None)
            if pope_template:
                print(f"   ✓ Pope Leo XIII template loaded: {pope_template.name}")
            else:
                print("   ✗ Pope Leo XIII template not found")
        
        print("   ✓ Database and templates working\n")
        
    except Exception as e:
        print(f"   ✗ Database error: {e}\n")
        return False
    finally:
        db.close()
    
    # Test 2: Agent Factory
    print("2️⃣ Testing Agent Factory...")
    try:
        db = get_db_session()
        agent_factory = AgentFactory(db)
        scenario_factory = ScenarioFactory(db)
        
        # Find Pope template
        manager = TemplateManager(db)
        pope_template = manager.get_agent_template_by_name("Pope Leo XIII")
        
        if pope_template:
            # Create a test scenario run first
            scenario_template = manager.get_scenario_template_by_name("Supernatural Vision Investigation")
            if scenario_template:
                scenario_run = scenario_factory.create_scenario_run(
                    template_id=scenario_template.id,
                    run_name="Test Run",
                    runtime_config={"test_mode": True}
                )
                
                # Create agent instance
                agent_instance = agent_factory.create_agent_instance(
                    template_id=pope_template.id,
                    scenario_run_id=scenario_run.id,
                    instance_name="Test Pope Leo XIII",
                    runtime_config={"test_mode": True}
                )
                
                print(f"   ✓ Created agent instance: {agent_instance.instance_name}")
                print("   ✓ Agent factory working\n")
            else:
                print("   ⚠️ No scenario template found for testing\n")
        else:
            print("   ⚠️ No Pope template found for testing\n")
            
    except Exception as e:
        print(f"   ✗ Agent factory error: {e}\n")
    finally:
        db.close()
    
    # Test 3: Base Engine (without actual LLM call)
    print("3️⃣ Testing Base Engine...")
    try:
        # Create a minimal agent config for testing
        test_config = {
            "personality_config": {
                "name": "Test Agent",
                "description": "A test agent",
                "instructions": "You are a helpful test assistant.",
                "agent_kwargs": {"markdown": True}
            },
            "model_config": {
                "id": "meta-llama/llama-3.1-8b-instruct:free",
                "temperature": 0.7
            },
            "tools_config": {}
        }
        
        engine = TestEngine(test_config)
        print("   ✓ Engine created successfully")
        
        # Test initialization (without calling LLM)
        print("   ✓ Engine initialization works")
        print("   ✓ Base engine working\n")
        
    except Exception as e:
        print(f"   ✗ Engine error: {e}\n")
    
    # Test 4: Configuration
    print("4️⃣ Testing Configuration...")
    try:
        # Test path configuration
        print(f"   Project root: {Config.PROJECT_ROOT}")
        print(f"   Data directory: {Config.DATA_DIR}")
        print(f"   Templates directory: {Config.TEMPLATES_DIR}")
        
        # Test model configuration
        openrouter_config = Config.get_model_config("openrouter")
        print(f"   OpenRouter default model: {openrouter_config['id']}")
        
        print("   ✓ Configuration working\n")
        
    except Exception as e:
        print(f"   ✗ Configuration error: {e}\n")
    
    print("🎉 Phase 1 Testing Complete!")
    print("\nNext steps:")
    print("- Set up OpenRouter API key for live testing")
    print("- Implement ActorEngine, NarratorEngine, AnalystEngine")
    print("- Create orchestration system")
    print("- Build FastAPI interface")


if __name__ == "__main__":
    asyncio.run(test_phase_1())
