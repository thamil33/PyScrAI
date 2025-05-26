"""
Integration test for template API endpoints
"""
import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pyscrai.databases.api.main import app
from pyscrai.databases.database import get_db
from pyscrai.databases.models.base import Base


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_templates.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="function")
def setup_database():
    """Set up test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestTemplateAPI:
    """Test suite for template API endpoints"""
    
    def test_create_agent_template(self, setup_database):
        """Test creating a new agent template"""
        template_data = {
            "name": "test_agent",
            "description": "A test agent template",
            "personality_config": {
                "role": "helpful assistant",
                "backstory": "An AI assistant designed to help users",
                "goals": ["help users", "provide accurate information"],
                "traits": {"helpful": True, "analytical": True},
                "instructions": ["be helpful", "be accurate"],
                "constraints": ["be truthful", "be safe"]
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 1000
            },
            "tools_config": {
                "calculator": {
                    "name": "calculator",
                    "enabled": True,
                    "config": {"precision": 10}
                }
            }
        }
        
        response = client.post("/api/v1/templates/agents", json=template_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["description"] == template_data["description"]
        assert data["id"] is not None
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_agent_template_validation_error(self, setup_database):
        """Test creating agent template with invalid data"""
        template_data = {
            "name": "",  # Invalid: empty name
            "description": "A test agent template",
            "personality_config": {
                "role": ""  # Invalid: empty role
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-4"
            }
        }
        
        response = client.post("/api/v1/templates/agents", json=template_data)
        assert response.status_code == 400
    
    def test_list_agent_templates(self, setup_database):
        """Test listing agent templates"""
        # Create a test template first
        template_data = {
            "name": "list_test_agent",
            "description": "Template for list test",
            "personality_config": {
                "role": "test role"
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-3.5-turbo"
            }
        }
        client.post("/api/v1/templates/agents", json=template_data)
        
        response = client.get("/api/v1/templates/agents")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == template_data["name"]
    
    def test_get_agent_template_by_id(self, setup_database):
        """Test getting agent template by ID"""
        # Create a test template first
        template_data = {
            "name": "get_by_id_test",
            "description": "Template for get by ID test",
            "personality_config": {
                "role": "test role"
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-3.5-turbo"
            }
        }
        create_response = client.post("/api/v1/templates/agents", json=template_data)
        created_template = create_response.json()
        
        response = client.get(f"/api/v1/templates/agents/{created_template['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == created_template["id"]
        assert data["name"] == template_data["name"]
    
    def test_get_agent_template_by_name(self, setup_database):
        """Test getting agent template by name"""
        # Create a test template first
        template_data = {
            "name": "get_by_name_test",
            "description": "Template for get by name test",
            "personality_config": {
                "role": "test role"
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-3.5-turbo"
            }
        }
        client.post("/api/v1/templates/agents", json=template_data)
        
        response = client.get(f"/api/v1/templates/agents/by-name/{template_data['name']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == template_data["name"]
    
    def test_update_agent_template(self, setup_database):
        """Test updating an agent template"""
        # Create a test template first
        template_data = {
            "name": "update_test",
            "description": "Original description",
            "personality_config": {
                "role": "test role"
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-3.5-turbo"
            }
        }
        create_response = client.post("/api/v1/templates/agents", json=template_data)
        created_template = create_response.json()
        
        # Update the template
        update_data = {
            "description": "Updated description",
            "personality_config": {
                "role": "updated role",
                "traits": {"new_trait": "updated"}
            }
        }
        
        response = client.put(
            f"/api/v1/templates/agents/{created_template['id']}", 
            json=update_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == update_data["description"]
        assert data["personality_config"]["role"] == "updated role"
        assert data["name"] == template_data["name"]  # Unchanged field
    
    def test_delete_agent_template(self, setup_database):
        """Test deleting an agent template"""
        # Create a test template first
        template_data = {
            "name": "delete_test",
            "description": "Template for delete test",
            "personality_config": {
                "role": "test role"
            },
            "llm_config": {
                "provider": "openai",
                "model_id": "gpt-3.5-turbo"
            }
        }
        create_response = client.post("/api/v1/templates/agents", json=template_data)
        created_template = create_response.json()
        
        # Delete the template
        response = client.delete(f"/api/v1/templates/agents/{created_template['id']}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "success"
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/templates/agents/{created_template['id']}")
        assert get_response.status_code == 404
    
    def test_create_scenario_template(self, setup_database):
        """Test creating a new scenario template"""
        template_data = {
            "name": "test_scenario",
            "description": "A test scenario template",
            "config": {
                "max_turns": 30,
                "timeout_seconds": 1800,
                "completion_conditions": {"all_agents_ready": True},
                "error_handling": {"retry_count": 3}
            },
            "agent_roles": {
                "teacher": {
                    "template_name": "teacher_template",
                    "role_config": {"subject": "math"},
                    "required": True
                },
                "students": {
                    "template_name": "student_template",
                    "role_config": {"grade_level": "10"},
                    "required": True
                }
            },
            "event_flow": {
                "introduction": {
                    "type": "trigger",
                    "source": "teacher",
                    "data_schema": {"message": "string"}
                },
                "lesson": {
                    "type": "interaction",
                    "source": "teacher",
                    "target": "students"
                }
            }
        }
        
        response = client.post("/api/v1/templates/scenarios", json=template_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == template_data["name"]
        assert data["description"] == template_data["description"]
        assert data["id"] is not None
    
    def test_scenario_template_crud_operations(self, setup_database):
        """Test full CRUD operations for scenario templates"""
        # Create
        template_data = {
            "name": "crud_test_scenario",
            "description": "Scenario for CRUD testing",
            "config": {
                "max_turns": 10,
                "timeout_seconds": 600
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
        
        create_response = client.post("/api/v1/templates/scenarios", json=template_data)
        assert create_response.status_code == 200
        created_template = create_response.json()
        
        # Read
        get_response = client.get(f"/api/v1/templates/scenarios/{created_template['id']}")
        assert get_response.status_code == 200
        
        # Update
        update_data = {"description": "Updated CRUD test scenario"}
        update_response = client.put(
            f"/api/v1/templates/scenarios/{created_template['id']}", 
            json=update_data
        )
        assert update_response.status_code == 200
        updated_template = update_response.json()
        assert updated_template["description"] == update_data["description"]
        
        # Delete
        delete_response = client.delete(f"/api/v1/templates/scenarios/{created_template['id']}")
        assert delete_response.status_code == 200
        
        # Verify deletion
        get_after_delete = client.get(f"/api/v1/templates/scenarios/{created_template['id']}")
        assert get_after_delete.status_code == 404
    
    def test_template_not_found_errors(self, setup_database):
        """Test 404 errors for non-existent templates"""
        # Test agent template not found
        response = client.get("/api/v1/templates/agents/99999")
        assert response.status_code == 404
        
        response = client.get("/api/v1/templates/agents/by-name/nonexistent")
        assert response.status_code == 404
        
        response = client.put("/api/v1/templates/agents/99999", json={"description": "test"})
        assert response.status_code == 404
        
        response = client.delete("/api/v1/templates/agents/99999")
        assert response.status_code == 404
        
        # Test scenario template not found
        response = client.get("/api/v1/templates/scenarios/99999")
        assert response.status_code == 404
        
        response = client.put("/api/v1/templates/scenarios/99999", json={"description": "test"})
        assert response.status_code == 404
        
        response = client.delete("/api/v1/templates/scenarios/99999")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
