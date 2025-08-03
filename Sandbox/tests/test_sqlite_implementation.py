#!/usr/bin/env python3
"""
Test script to verify SQLite persistence with JSON schema support.
"""

import tempfile
import json
from pathlib import Path
from datetime import datetime

from simulation_framework.state import SimulationState, AgentState, Message, SQLitePersistence


def test_sqlite_json_schema_support():
    """Test SQLite persistence with complex JSON schema support."""
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)
    
    try:
        # Initialize SQLite persistence
        persistence = SQLitePersistence(db_path)
        
        # Create a complex state with nested JSON structures
        complex_state = SimulationState(
            simulation_id="json-schema-test",
            timestamp=datetime.now(),
            agents={
                "research_agent": AgentState(
                    name="ResearchAgent",
                    agent_type="research",
                    status="active",
                    memory={
                        "hypotheses": [
                            {"id": 1, "text": "AI improves productivity", "confidence": 0.8},
                            {"id": 2, "text": "Remote work reduces costs", "confidence": 0.9}
                        ],
                        "experiments": {
                            "exp_001": {
                                "design": {"participants": 100, "duration_days": 30},
                                "results": {"p_value": 0.03, "effect_size": 0.25}
                            }
                        }
                    }
                ),
                "moderator_agent": AgentState(
                    name="ModeratorAgent",
                    agent_type="moderator",
                    status="waiting",
                    memory={
                        "debate_rules": {
                            "time_limit_minutes": 30,
                            "max_arguments": 5,
                            "evidence_required": True
                        }
                    }
                )
            },
            conversation_log=[
                Message(
                    id="msg_001",
                    sender="research_agent",
                    content="I propose we test the hypothesis about AI productivity gains",
                    timestamp=datetime.now(),
                    metadata={
                        "message_type": "hypothesis_proposal",
                        "confidence": 0.85,
                        "references": ["doi:10.1000/example", "arxiv:2024.0001"]
                    }
                ),
                Message(
                    id="msg_002",
                    sender="moderator_agent", 
                    content="That's an excellent research direction. Let's design an experiment",
                    timestamp=datetime.now(),
                    metadata={
                        "message_type": "approval",
                        "next_action": "experiment_design"
                    }
                )
            ],
            shared_context={
                "research_domain": "AI productivity",
                "experimental_config": {
                    "randomization": True,
                    "blinding": "single",
                    "statistical_power": 0.8
                },
                "collaboration_network": {
                    "primary_researchers": ["agent_1", "agent_2"],
                    "peer_reviewers": ["agent_3", "agent_4"],
                    "methodology_experts": ["agent_5"]
                }
            },
            user_input="Please proceed with the experiment design phase",
            metadata={
                "module_type": "research",
                "simulation_mode": "realistic",
                "data_generation": {
                    "distribution": "normal",
                    "noise_level": 0.1,
                    "sample_size": 1000
                },
                "quality_metrics": {
                    "reproducibility_score": 0.92,
                    "validity_score": 0.88,
                    "statistical_rigor": 0.95
                }
            }
        )
        
        print("✓ Created complex state with nested JSON structures")
        
        # Save the state
        persistence.save_state(complex_state)
        print("✓ Saved complex state to SQLite")
        
        # Load the state back
        loaded_state = persistence.load_state("json-schema-test")
        print("✓ Loaded state from SQLite")
        
        # Verify complex nested structures are preserved
        assert loaded_state is not None
        assert loaded_state.simulation_id == "json-schema-test"
        
        # Check agent memory structures
        research_agent = loaded_state.agents["research_agent"]
        assert len(research_agent.memory["hypotheses"]) == 2
        assert research_agent.memory["hypotheses"][0]["confidence"] == 0.8
        assert research_agent.memory["experiments"]["exp_001"]["results"]["p_value"] == 0.03
        print("✓ Agent memory structures preserved correctly")
        
        # Check message metadata
        msg1 = loaded_state.conversation_log[0]
        assert msg1.metadata["confidence"] == 0.85
        assert "doi:10.1000/example" in msg1.metadata["references"]
        print("✓ Message metadata preserved correctly")
        
        # Check shared context
        assert loaded_state.shared_context["experimental_config"]["statistical_power"] == 0.8
        assert "agent_3" in loaded_state.shared_context["collaboration_network"]["peer_reviewers"]
        print("✓ Shared context structures preserved correctly")
        
        # Check metadata
        assert loaded_state.metadata["data_generation"]["noise_level"] == 0.1
        assert loaded_state.metadata["quality_metrics"]["reproducibility_score"] == 0.92
        print("✓ Simulation metadata preserved correctly")
        
        # Test partial updates with complex nested structures
        updates = {
            "shared_context": {
                "experimental_config": {
                    "statistical_power": 0.9,  # Update existing
                    "effect_size_threshold": 0.2  # Add new
                }
            },
            "metadata": {
                "quality_metrics": {
                    "reproducibility_score": 0.95  # Update existing
                }
            }
        }
        
        persistence.update_state("json-schema-test", updates)
        updated_state = persistence.load_state("json-schema-test")
        
        # Verify updates were applied correctly
        assert updated_state.shared_context["experimental_config"]["statistical_power"] == 0.9
        assert updated_state.shared_context["experimental_config"]["effect_size_threshold"] == 0.2
        assert updated_state.metadata["quality_metrics"]["reproducibility_score"] == 0.95
        # Verify other data wasn't lost
        assert "collaboration_network" in updated_state.shared_context  # Verify other data preserved
        assert updated_state.metadata["quality_metrics"]["validity_score"] == 0.88
        print("✓ Partial updates with nested structures work correctly")
        
        # Test versioning
        assert updated_state.version == 2
        print("✓ State versioning working")
        
        # Test snapshots
        snapshot_id = persistence.create_snapshot("json-schema-test", "after_updates")
        restored_state = persistence.restore_snapshot(snapshot_id)
        assert restored_state.shared_context["experimental_config"]["statistical_power"] == 0.9
        print("✓ Snapshots preserve complex JSON structures")
        
        # Test history
        history = persistence.get_state_history("json-schema-test")
        assert len(history) == 2  # Original + updated
        assert history[0].version == 1
        assert history[1].version == 2
        print("✓ State history tracking works")
        
        # Test large conversation log performance
        large_log = []
        for i in range(500):
            large_log.append(Message(
                id=f"perf_msg_{i}",
                sender=f"agent_{i % 3}",
                content=f"Performance test message {i} with complex metadata",
                timestamp=datetime.now(),
                metadata={
                    "test_iteration": i,
                    "performance_data": {
                        "latency_ms": i * 1.5,
                        "memory_usage_mb": i * 0.8,
                        "cpu_percent": (i % 100) / 100
                    },
                    "nested_structure": {
                        "level_1": {"level_2": {"level_3": f"value_{i}"}}
                    }
                }
            ))
        
        perf_state = SimulationState(
            simulation_id="performance-test",
            timestamp=datetime.now(),
            agents={
                "agent_0": AgentState(name="agent_0", agent_type="test", total_messages=167),
                "agent_1": AgentState(name="agent_1", agent_type="test", total_messages=167),
                "agent_2": AgentState(name="agent_2", agent_type="test", total_messages=166),
            },
            conversation_log=large_log,
            shared_context={},
            metadata={}
        )
        
        import time
        start_time = time.time()
        persistence.save_state(perf_state)
        save_time = time.time() - start_time
        
        start_time = time.time()
        loaded_perf_state = persistence.load_state("performance-test")
        load_time = time.time() - start_time
        
        assert len(loaded_perf_state.conversation_log) == 500
        assert loaded_perf_state.conversation_log[499].metadata["test_iteration"] == 499
        assert loaded_perf_state.agents["agent_0"].total_messages == 167
        assert loaded_perf_state.agents["agent_1"].total_messages == 167
        assert loaded_perf_state.agents["agent_2"].total_messages == 166
        print(f"✓ Performance test: Save {save_time:.3f}s, Load {load_time:.3f}s for 500 complex messages")
        
        print("\n🎉 All SQLite JSON schema tests passed!")
        
    finally:
        # Clean up
        if db_path.exists():
            db_path.unlink()


if __name__ == "__main__":
    test_sqlite_json_schema_support()