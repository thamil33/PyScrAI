"""
Comprehensive tests for the updated template validators and schemas aligned with universal generic templates
"""

import json
import pytest
from pathlib import Path
from pyscrai.databases.models.template_validators import (
    AgentTemplateValidator, 
    ScenarioTemplateValidator,
    UniversalAgentTemplateValidator,
    EngineType,
    RuntimeOverridePolicy,
    ActorEngineConfig,
    AnalystEngineConfig,
    NarratorEngineConfig
)
from pyscrai.databases.models.schemas import (
    AgentTemplateCreate,
    AgentTemplateResponse,
    ScenarioTemplateCreate,
    TemplateValidationRequest,
    RuntimeConfigurationRequest
)


class TestUniversalTemplateValidation:
    """Test the updated template validation system"""
    
    @pytest.fixture
    def template_dir(self):
        return Path("pyscrai/templates")
    
    @pytest.fixture
    def generic_actor_template(self, template_dir):
        with open(template_dir / "agents" / "generic_actor.json", 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def generic_analyst_template(self, template_dir):
        with open(template_dir / "agents" / "generic_analyst.json", 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def generic_narrator_template(self, template_dir):
        with open(template_dir / "agents" / "generic_narrator.json", 'r') as f:
            return json.load(f)
    
    @pytest.fixture
    def generic_conversation_scenario(self, template_dir):
        with open(template_dir / "scenarios" / "generic_conversation.json", 'r') as f:
            return json.load(f)
    
    def test_generic_actor_validation(self, generic_actor_template):
        """Test validation of generic actor template"""
        validated = AgentTemplateValidator(**generic_actor_template)
        
        assert validated.name == "Generic Actor"
        assert validated.engine_type == EngineType.ACTOR
        assert validated.runtime_overrides is not None
        assert len(validated.tools_config) > 0
        assert "reasoning" in validated.tools_config
        assert "memory" in validated.tools_config
    
    def test_generic_analyst_validation(self, generic_analyst_template):
        """Test validation of generic analyst template"""
        validated = AgentTemplateValidator(**generic_analyst_template)
        
        assert validated.name == "Generic Analyst"
        assert validated.engine_type == EngineType.ANALYST
        assert validated.runtime_overrides is not None
        assert len(validated.tools_config) > 0
        assert "pattern_analysis" in validated.tools_config
        assert "metrics_tracking" in validated.tools_config
        assert "insight_generation" in validated.tools_config
    
    def test_generic_narrator_validation(self, generic_narrator_template):
        """Test validation of generic narrator template"""
        validated = AgentTemplateValidator(**generic_narrator_template)
        
        assert validated.name == "Generic Narrator"
        assert validated.engine_type == EngineType.NARRATOR
        assert validated.runtime_overrides is not None
        assert len(validated.tools_config) > 0
        assert "description_generation" in validated.tools_config
        assert "scene_transitions" in validated.tools_config
    
    def test_generic_conversation_scenario_validation(self, generic_conversation_scenario):
        """Test validation of generic conversation scenario"""
        validated = ScenarioTemplateValidator(**generic_conversation_scenario)
        
        assert validated.name == "GenericConversation"
        assert len(validated.agent_roles) == 4
        assert len(validated.event_flow) == 5
        assert validated.runtime_customization is not None
        
        # Check agent roles
        assert "primary_actor" in validated.agent_roles
        assert "secondary_actor" in validated.agent_roles
        assert "narrator" in validated.agent_roles
        assert "analyst" in validated.agent_roles
        
        # Check event flow
        assert "scenario_initialization" in validated.event_flow
        assert "scene_setting" in validated.event_flow
        assert "conversation_turn" in validated.event_flow
        assert "analysis_checkpoint" in validated.event_flow
        assert "scenario_conclusion" in validated.event_flow
    
    def test_engine_specific_validation(self):
        """Test engine-specific configuration validation"""
        
        # Test Actor engine config
        actor_config = ActorEngineConfig(
            character_reasoning=True,
            context_window=15,
            emotional_modeling=True,
            relationship_tracking=True
        )
        assert actor_config.character_reasoning is True
        assert actor_config.context_window == 15
        
        # Test Analyst engine config
        analyst_config = AnalystEngineConfig(
            default_metrics=["custom_metric1", "custom_metric2"],
            analysis_frequency=3,
            behavioral_patterns=True
        )
        assert len(analyst_config.default_metrics) == 2
        assert analyst_config.analysis_frequency == 3
        
        # Test Narrator engine config
        narrator_config = NarratorEngineConfig(
            sensory_details=True,
            atmospheric_focus=True,
            default_perspective="first_person",
            narrative_style="poetic"
        )
        assert narrator_config.default_perspective == "first_person"
        assert narrator_config.narrative_style == "poetic"
    
    def test_runtime_override_policies(self):
        """Test runtime override policy validation"""
        
        # Test all override policies
        policies = [
            RuntimeOverridePolicy.OVERRIDE_ALLOWED,
            RuntimeOverridePolicy.MERGE_ALLOWED,
            RuntimeOverridePolicy.APPEND_ALLOWED,
            RuntimeOverridePolicy.FORBIDDEN
        ]
        
        for policy in policies:
            assert isinstance(policy.value, str)
            assert policy.value in ["override_allowed", "merge_allowed", "append_allowed", "forbidden"]
    
    def test_schema_compatibility(self, generic_actor_template):
        """Test that templates work with API schemas"""
        
        # Test AgentTemplateCreate schema
        create_data = {
            "name": generic_actor_template["name"],
            "description": generic_actor_template["description"],
            "engine_type": generic_actor_template["engine_type"],
            "personality_config": generic_actor_template["personality_config"],
            "llm_config": generic_actor_template["llm_config"],
            "tools_config": generic_actor_template["tools_config"],
            "runtime_overrides": generic_actor_template["runtime_overrides"]
        }
        
        create_schema = AgentTemplateCreate(**create_data)
        assert create_schema.name == "Generic Actor"
        assert create_schema.engine_type == EngineType.ACTOR
    
    def test_template_validation_request_schema(self, generic_actor_template):
        """Test template validation request schema"""
        
        validation_request = TemplateValidationRequest(
            template_type="agent",
            template_data=generic_actor_template,
            strict_validation=True
        )
        
        assert validation_request.template_type == "agent"
        assert validation_request.strict_validation is True
        assert validation_request.template_data["name"] == "Generic Actor"
    
    def test_runtime_configuration_request_schema(self):
        """Test runtime configuration request schema"""
        
        config_request = RuntimeConfigurationRequest(
            agent_instance_id=1,
            configuration_updates={
                "personality_config": {
                    "role": "updated_character",
                    "traits": {"new_trait": "value"}
                }
            },
            override_policies={
                "personality_config": RuntimeOverridePolicy.MERGE_ALLOWED
            },
            validate_before_apply=True
        )
        
        assert config_request.agent_instance_id == 1
        assert config_request.validate_before_apply is True
        assert config_request.override_policies["personality_config"] == RuntimeOverridePolicy.MERGE_ALLOWED
    
    def test_invalid_template_validation(self):
        """Test validation with invalid template data"""
        
        # Test missing required fields
        with pytest.raises(ValueError):
            AgentTemplateValidator(
                name="",  # Empty name should fail
                engine_type=EngineType.ACTOR,
                personality_config={"role": "test"},
                llm_config={"provider": "openai", "model_id": "gpt-4"}
            )
        
        # Test invalid engine type combination
        with pytest.raises(ValueError):
            from pyscrai.databases.models.template_validators import EngineSpecificValidator
            
            UniversalAgentTemplateValidator(
                name="Test Agent",
                engine_type=EngineType.ACTOR,
                personality_config={"role": "test"},
                llm_config={"provider": "openai", "model_id": "gpt-4"},
                engine_specific_config=EngineSpecificValidator(
                    analyst=AnalystEngineConfig()  # Should fail for actor engine
                )
            )
    
    def test_scenario_validation_requirements(self):
        """Test scenario validation requirements"""
        
        # Test scenario with no agent roles (should fail)
        with pytest.raises(ValueError):
            ScenarioTemplateValidator(
                name="Test Scenario",
                config={"max_turns": 10, "timeout_seconds": 3600},
                agent_roles={},  # Empty roles should fail
                event_flow={"test_event": {
                    "type": "system",
                    "source": "system",
                    "target": "all",
                    "conditions": {"trigger": "start"}
                }}
            )
        
        # Test scenario with no system events (should fail)
        with pytest.raises(ValueError):
            ScenarioTemplateValidator(
                name="Test Scenario",
                config={"max_turns": 10, "timeout_seconds": 3600},
                agent_roles={"test_role": {
                    "template_name": "Generic Actor",
                    "engine_type": "actor",
                    "required": True
                }},
                event_flow={"test_event": {
                    "type": "interaction",  # No system event
                    "source": "agent",
                    "target": "other",
                    "conditions": {"trigger": "start"}
                }}
            )


if __name__ == "__main__":
    # Run basic validation tests
    test_instance = TestUniversalTemplateValidation()
    
    # Load templates
    template_dir = Path("pyscrai/templates")
    
    with open(template_dir / "agents" / "generic_actor.json", 'r') as f:
        actor_template = json.load(f)
    
    with open(template_dir / "agents" / "generic_analyst.json", 'r') as f:
        analyst_template = json.load(f)
    
    with open(template_dir / "agents" / "generic_narrator.json", 'r') as f:
        narrator_template = json.load(f)
    
    with open(template_dir / "scenarios" / "generic_conversation.json", 'r') as f:
        conversation_scenario = json.load(f)
    
    print("Running comprehensive template validation tests...")
    
    # Test all agent templates
    print("\n1. Testing Generic Actor template...")
    test_instance.test_generic_actor_validation(actor_template)
    print("✓ Generic Actor validation passed")
    
    print("\n2. Testing Generic Analyst template...")
    test_instance.test_generic_analyst_validation(analyst_template)
    print("✓ Generic Analyst validation passed")
    
    print("\n3. Testing Generic Narrator template...")
    test_instance.test_generic_narrator_validation(narrator_template)
    print("✓ Generic Narrator validation passed")
    
    print("\n4. Testing Generic Conversation scenario...")
    test_instance.test_generic_conversation_scenario_validation(conversation_scenario)
    print("✓ Generic Conversation scenario validation passed")
    
    print("\n5. Testing engine-specific configurations...")
    test_instance.test_engine_specific_validation()
    print("✓ Engine-specific configuration validation passed")
    
    print("\n6. Testing runtime override policies...")
    test_instance.test_runtime_override_policies()
    print("✓ Runtime override policy validation passed")
    
    print("\n7. Testing schema compatibility...")
    test_instance.test_schema_compatibility(actor_template)
    print("✓ Schema compatibility validation passed")
    
    print("\n8. Testing template validation request schema...")
    test_instance.test_template_validation_request_schema(actor_template)
    print("✓ Template validation request schema passed")
    
    print("\n9. Testing runtime configuration request schema...")
    test_instance.test_runtime_configuration_request_schema()
    print("✓ Runtime configuration request schema passed")
    
    print("\n🎉 All comprehensive template validation tests passed!")
    print("\nThe updated template validators and schemas are fully compatible with:")
    print("  • Universal generic templates (Actor, Analyst, Narrator)")
    print("  • Custom engine types and configurations")
    print("  • Runtime override policies")
    print("  • Enhanced API schemas")
    print("  • Comprehensive validation rules")
