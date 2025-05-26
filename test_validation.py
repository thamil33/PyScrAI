"""
Simple validation test to understand the current template validation requirements
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from pyscrai.databases.models.template_validators import AgentTemplateValidator, ScenarioTemplateValidator

def test_agent_template_validation():
    """Test what data structure is expected for agent templates"""
    # Try minimal valid data
    minimal_data = {
        "name": "test_agent",
        "personality_config": {
            "role": "test_role"
        },
        "llm_config": {
            "provider": "openai",
            "model_id": "gpt-3.5-turbo"
        }
    }
    
    try:
        validator = AgentTemplateValidator(**minimal_data)
        print("✓ Minimal agent template validation passed")
        print(f"Validated data: {validator}")
        return True
    except Exception as e:
        print(f"✗ Agent template validation failed: {e}")
        return False

def test_scenario_template_validation():
    """Test what data structure is expected for scenario templates"""
    # Try minimal valid data
    minimal_data = {
        "name": "test_scenario",
        "config": {
            "max_turns": 10,
            "timeout_seconds": 300
        },
        "agent_roles": {
            "agent1": {
                "template_name": "test_template"
            }
        },
        "event_flow": {
            "event1": {
                "type": "trigger"
            }
        }
    }
    
    try:
        validator = ScenarioTemplateValidator(**minimal_data)
        print("✓ Minimal scenario template validation passed")
        print(f"Validated data: {validator}")
        return True
    except Exception as e:
        print(f"✗ Scenario template validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing template validation requirements...")
    print()
    
    agent_valid = test_agent_template_validation()
    print()
    scenario_valid = test_scenario_template_validation()
    
    if agent_valid and scenario_valid:
        print("\n✓ All validations passed! The validation schemas are working.")
    else:
        print("\n✗ Some validations failed. Check the required data structures.")
