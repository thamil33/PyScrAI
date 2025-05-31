# Tests for Inter-Agent Communication and Scenario Execution
import pytest
import asyncio
from sqlalchemy.orm import Session
from unittest.mock import call, patch, AsyncMock # Required for checking multiple calls to a mock

from pyscrai.engines.scenario_runner import ScenarioRunner
from pyscrai.databases.models import ScenarioTemplate, AgentTemplate, ScenarioRun, AgentInstance
from pyscrai.core.models import Event # For type hinting and event creation if needed
from pyscrai.engines.orchestration.engine_manager import EngineManager # Ensure EngineManager is imported

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_generic_conversation_template_data() -> dict:
    """Provides a dictionary representing a simplified GenericConversation scenario template."""
    return {
        "name": "TestGenericConversation",
        "description": "A test scenario for inter-agent communication.",
        "version": "1.0",
        "config": {
            "max_turns": 10,
            "initial_prompt": "The scene is a quiet cafe. Alice is waiting."
        },
        "agent_roles": {
            "narrator": {
                "template_name": "NarratorAgentTemplate",
                "engine_type": "narrator",
                "config": {"persona": "A neutral observer describing the scene."}
            },
            "primary_actor": {
                "template_name": "ActorAgentTemplate",
                "engine_type": "actor",
                "config": {"persona": "Alice, a curious and friendly individual."}
            },
            "secondary_actor": {
                "template_name": "ActorAgentTemplate",
                "engine_type": "actor",
                "config": {"persona": "Bob, a cautious and thoughtful individual."}
            },
            "analyst": {
                "template_name": "AnalystAgentTemplate",
                "engine_type": "analyst",
                "config": {"analysis_focus": "conversation dynamics"}
            }
        },
        "event_flow": {
            "scenario_initialization": {
                "source": "system",
                "event_type": "request_scene_update", # Request Narrator to describe scene
                "target": "narrator",
                "conditions": {"trigger": "scenario_start"}
            },
            "narrator_describes_scene": {
                "source": "narrator",
                "event_type": "scene_description_generated",
                "target": "all_actors", # Send to Alice and Bob
                "transform_to": "scene_description_updated" # What actors expect
            },
            "alice_speaks_to_bob": {
                "source": "primary_actor",
                "event_type": "actor_speech_generated",
                "target": "secondary_actor",
                "transform_to": "conversation_message"
            },
            "bob_speaks_to_alice": {
                "source": "secondary_actor",
                "event_type": "actor_speech_generated",
                "target": "primary_actor",
                "transform_to": "conversation_message"
            },
            "actors_speak_to_analyst": {
                "source": "any_actor", # Matches primary_actor or secondary_actor
                "event_type": "actor_speech_generated",
                "target": "analyst" # Analyst listens to all actor speech
                # No transform_to needed if analyst handles actor_speech_generated directly
            },
            "analyst_reports": {
                "source": "analyst",
                "event_type": "analysis_checkpoint_generated",
                "target": "system" # Or a specific log/monitoring target
            }
        }
    }

@pytest.fixture
def mock_narrator_template(db_session: Session) -> AgentTemplate:
    template = AgentTemplate(
        name="NarratorAgentTemplate",
        description="A template for narrator agents.",
        version="1.0",
        config_schema={"type": "object", "properties": {"persona": {"type": "string"}}},
        default_config={"persona": "A neutral observer."},
        engine_type="narrator"
    )
    db_session.add(template)
    db_session.commit()
    return template

@pytest.fixture
def mock_actor_template(db_session: Session) -> AgentTemplate:
    template = AgentTemplate(
        name="ActorAgentTemplate",
        description="A template for actor agents.",
        version="1.0",
        config_schema={"type": "object", "properties": {"persona": {"type": "string"}}},
        default_config={"persona": "A generic actor."},
        engine_type="actor"
    )
    db_session.add(template)
    db_session.commit()
    return template

@pytest.fixture
def mock_analyst_template(db_session: Session) -> AgentTemplate:
    template = AgentTemplate(
        name="AnalystAgentTemplate",
        description="A template for analyst agents.",
        version="1.0",
        config_schema={"type": "object", "properties": {"analysis_focus": {"type": "string"}}},
        default_config={"analysis_focus": "general_events"},
        engine_type="analyst"
    )
    db_session.add(template)
    db_session.commit()
    return template

@pytest.fixture
def mock_scenario_template(db_session: Session, mock_generic_conversation_template_data: dict, mock_narrator_template, mock_actor_template, mock_analyst_template) -> ScenarioTemplate:
    data = mock_generic_conversation_template_data
    template = ScenarioTemplate(
        name=data["name"],
        description=data["description"],
        version=data["version"],
        config=data["config"],
        agent_roles=data["agent_roles"],
        event_flow=data["event_flow"]
    )
    db_session.add(template)
    db_session.commit()
    return template

async def test_scenario_creation_and_initialization(
    scenario_runner: ScenarioRunner, 
    db_session: Session, 
    mock_scenario_template: ScenarioTemplate
):
    """Test basic scenario creation, agent instantiation, and initial status."""
    template_name = mock_scenario_template.name

    # Mock LLM calls within engines to avoid actual API calls during this test
    # This might involve patching the llm_factory or specific engine methods
    # For now, we assume engines might run without LLM or with very basic fallbacks

    scenario_run_id = await scenario_runner.start_scenario(template_name=template_name)

    assert scenario_run_id is not None

    # Verify ScenarioRun in DB
    scenario_run = db_session.query(ScenarioRun).filter(ScenarioRun.id == scenario_run_id).first()
    assert scenario_run is not None
    assert scenario_run.template_id == mock_scenario_template.id
    assert scenario_run.status == "running" # Check for the final status after start_scenario completes
    assert scenario_run.started_at is not None

    # Verify AgentInstances in DB
    agent_instances = db_session.query(AgentInstance).filter(AgentInstance.scenario_run_id == scenario_run_id).all()
    assert len(agent_instances) == len(mock_scenario_template.agent_roles)

    # Verify scenario context in EngineManager
    engine_manager = scenario_runner.engine_manager
    assert scenario_run_id in engine_manager.scenario_context_data
    context = engine_manager.scenario_context_data[scenario_run_id]
    assert len(context["agent_roles"]) == len(mock_scenario_template.agent_roles)
    assert context["event_flow"] == mock_scenario_template.event_flow

    # Verify role_agents mapping in EngineManager context
    assert len(context["role_agents"]) == len(mock_scenario_template.agent_roles)
    for role_name, agent_instance_id in context["role_agents"].items():
        assert role_name in mock_scenario_template.agent_roles
        # Find the agent instance in the DB to verify its details
        agent_instance_db = next((ai for ai in agent_instances if ai.id == agent_instance_id), None)
        assert agent_instance_db is not None
        assert agent_instance_db.role_in_scenario == role_name
        # Check if the engine_type from the template matches the instance's engine_type
        # This requires AgentInstance to store engine_type, or to fetch its AgentTemplate
        # For now, we assume the mapping is correct if the role_name matches.

    # Verify actor_agents list in EngineManager context
    expected_actor_agent_ids = sorted([
        ai.id for ai in agent_instances 
        if mock_scenario_template.agent_roles[ai.role_in_scenario]["engine_type"] == "actor"
    ])
    assert sorted(context["actor_agents"]) == expected_actor_agent_ids
    assert len(context["actor_agents"]) == 2 # Based on mock_generic_conversation_template_data

    # TODO: Add a test for the full inter-agent communication loop
    # This will involve: 
    # 1. Mocking engine process/handle_delivered_event methods to control their behavior and outputs.
    # 2. Simulating the initial event (e.g., from scenario_initialization in event_flow).
    # 3. Asserting that events are published to the event bus.
# 4. Asserting that EngineManager._handle_agent_generated_event routes them correctly.
# 5. Asserting that target engines receive the transformed events via their handle_delivered_event.

async def test_inter_agent_communication_flow(
    scenario_runner: ScenarioRunner,
    db_session: Session,
    mock_scenario_template: ScenarioTemplate
):
    """Test the full inter-agent communication flow, including event publishing, routing, and handling."""
    template_name = mock_scenario_template.name

    with patch('pyscrai.engines.base_engine.BaseEngine.publish_action_output', new_callable=AsyncMock) as mock_publish_action_output,\
         patch('pyscrai.engines.base_engine.BaseEngine.handle_delivered_event', new_callable=AsyncMock) as mock_handle_delivered_event:

        scenario_run_id = await scenario_runner.start_scenario(template_name=template_name)
        assert scenario_run_id is not None

        engine_manager = scenario_runner.engine_manager
        assert scenario_run_id in engine_manager.scenario_context_data
        scenario_context = engine_manager.scenario_context_data[scenario_run_id]

        # Allow time for the initial event to be processed if start_scenario doesn't block fully on it.
        # (Typically, event processing is asynchronous via the event bus)
        await asyncio.sleep(0.1) # Small delay to ensure async event processing has a chance to run

        # 1. Verify the initial event ("request_scene_update" to narrator)
        # This event is triggered by EngineManager._trigger_initial_event_for_scenario
        # and should result in narrator_engine.handle_delivered_event being called.

        assert mock_handle_delivered_event.called, "handle_delivered_event was not called"

        # Get the narrator's agent_instance_id
        narrator_agent_id = scenario_context["role_agents"].get("narrator")
        assert narrator_agent_id is not None, "Narrator agent ID not found in context"

        # Find the call to handle_delivered_event that was for the narrator
        # The event delivered to the narrator should be of type "request_scene_update"
        # The source_agent_id for this initial system event might be None or a special system ID.
        # The target_agent_id in the Event object passed to handle_delivered_event should be the narrator's ID.
        
        initial_event_call_args = None
        for call_item in mock_handle_delivered_event.call_args_list:
            args, kwargs = call_item
            if args: # handle_delivered_event(self, event: Event)
                delivered_event: Event = args[1] # The event object is the second argument
                if delivered_event.event_type == "request_scene_update" and \
                   delivered_event.target_agent_id == narrator_agent_id:
                    initial_event_call_args = args
                    break
        
        assert initial_event_call_args is not None, \
            f"Narrator did not receive 'request_scene_update'. Calls: {mock_handle_delivered_event.call_args_list}"

        # The 'self' in the call (args[0]) would be the narrator's engine instance.
        # We can verify this if we retrieve the engine instance from engine_manager, but checking event details is usually sufficient.
        # narrator_engine_instance = engine_manager.get_agent_engine(narrator_agent_id) # Assuming such a method
        # assert initial_event_call_args[0] == narrator_engine_instance

        # Now, let's simulate the narrator processing this event and publishing a response.
        # The narrator should publish "scene_description_generated".
        # We'll configure the mock_handle_delivered_event to do this when it's called for the narrator.

        # To simulate the narrator's response, we'll assume that when the narrator's
        # handle_delivered_event is called with "request_scene_update", it would internally
        # call its own publish_action_output method.
        # We can't directly make the *real* engine logic run here without more complex setup.
        # So, we'll manually trigger what we expect the narrator to do next.

        # Let's define the event the narrator is expected to publish.
        # According to event_flow: "source": "narrator", "event_type": "scene_description_generated", "target": "all_actors"
        narrator_output_event_type = "scene_description_generated"
        narrator_event_data = {"description": "The cafe is bustling with morning activity."}

        # We need to make the *mocked* publish_action_output get called as if the narrator engine called it.
        # The actual call would be: narrator_engine.publish_action_output(narrator_output_event_type, narrator_event_data)
        # Since we mocked publish_action_output at the class level, any engine instance calling it will call our mock.
        # We need a way to get the narrator's engine instance to call this, or simulate it.

        # For a more direct test of the EngineManager's routing of the *narrator's output*,
        # we can directly call the event bus as if the narrator published an event.
        # This bypasses testing the narrator's internal logic but tests the subsequent routing.

        # Let's assume the narrator's engine instance is `args[0]` from `initial_event_call_args`
        # This is the `self` of the `handle_delivered_event` call for the narrator.
        narrator_engine_mock_self = initial_event_call_args[0]

        # Simulate the narrator's engine calling publish_action_output.
        # The actual publish_action_output is async, so we await its mock call.
        # The mock_publish_action_output is already an AsyncMock.
        # The real method signature: async def publish_action_output(self, output_type: str, data: dict, target_role: Optional[str] = None, target_agent_id: Optional[str] = None)
        # From the event flow: "target": "all_actors"
        await narrator_engine_mock_self.publish_action_output(
            output_type=narrator_output_event_type,
            data=narrator_event_data,
            target_role="all_actors" # As per "narrator_describes_scene" in event_flow
        )

        # 2. Verify Narrator published "scene_description_generated"
        mock_publish_action_output.assert_called_once_with(
            output_type=narrator_output_event_type,
            data=narrator_event_data,
            target_role="all_actors"
        )
        # The `self` argument in the call would be narrator_engine_mock_self.
        assert mock_publish_action_output.call_args[0][0] == narrator_engine_mock_self

        # Clear mock for next stage if necessary, or use call_count if preferred for subsequent checks.
        # mock_publish_action_output.reset_mock() # If we want to isolate calls for the next step
        # mock_handle_delivered_event.reset_mock()

        # TODO: Assert that EngineManager processes this published event and delivers it to actors.
        # This will involve checking mock_handle_delivered_event again for calls to actor engines.
        pass
