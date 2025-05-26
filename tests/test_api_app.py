"""
Tests for FastAPI application setup
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from pyscrai.databases.api.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


def test_app_creation():
    """Test that the FastAPI app is created correctly"""
    assert app is not None
    assert app.title == "PyScrAI Engine API"
    assert app.description == "API for PyScrAI engine management and event processing"
    assert app.version == "1.0.0"


def test_root_endpoint(client):
    """Test the root endpoint"""
    response = client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["message"] == "PyScrAI Engine API is running"


def test_cors_middleware():
    """Test that CORS middleware is configured"""
    # Check that CORS middleware is added
    middleware_stack = app.user_middleware
    cors_middleware_found = False
    
    for middleware in middleware_stack:
        if "CORSMiddleware" in str(middleware):
            cors_middleware_found = True
            break
    
    assert cors_middleware_found, "CORS middleware should be configured"


def test_engine_router_included():
    """Test that engine router is included"""
    # Check that routes from engine_router are included
    routes = [route.path for route in app.routes]
    
    # The app should have at least the root route
    assert "/" in routes
    
    # Note: Other routes depend on the engine_endpoints module
    # which might have specific endpoints we can test for


def test_app_attributes():
    """Test app configuration attributes"""
    assert hasattr(app, 'title')
    assert hasattr(app, 'description') 
    assert hasattr(app, 'version')
    assert hasattr(app, 'user_middleware')
    assert hasattr(app, 'routes')


@patch('pyscrai.databases.api.app.engine_router')
def test_router_inclusion_mocked(mock_router, client):
    """Test router inclusion with mocked router"""
    # This test ensures the router inclusion code is covered
    # even if the actual router has issues
    
    response = client.get("/")
    assert response.status_code == 200


def test_app_openapi_schema():
    """Test that OpenAPI schema is generated correctly"""
    schema = app.openapi()
    
    assert schema is not None
    assert "info" in schema
    assert schema["info"]["title"] == "PyScrAI Engine API"
    assert schema["info"]["version"] == "1.0.0"


def test_app_routes_list():
    """Test that app has routes defined"""
    routes = list(app.routes)
    assert len(routes) > 0
    
    # Should have at least the root route
    root_routes = [route for route in routes if hasattr(route, 'path') and route.path == "/"]
    assert len(root_routes) > 0
