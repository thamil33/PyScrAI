# PyScrAI Tests

This directory contains the test suite for PyScrAI.

## Test Structure

- **`conftest.py`** - Test configuration and fixtures
- **`test_basic.py`** - Basic functionality tests (version, config, database)
- **`test_engines.py`** - Engine system tests
- **`test_factories.py`** - Factory classes tests (TemplateManager, etc.)
- **`test_integration.py`** - Integration tests for components working together

## Running Tests

From the project root directory:

```powershell
# Activate virtual environment
C:\Users\tyler\dev\PyScrAI\agno\.venv\Scripts\python.exe

# Run all tests
C:\Users\tyler\dev\PyScrAI\agno\.venv\Scripts\python.exe -m pytest tests/ -v

# Run specific test file
C:\Users\tyler\dev\PyScrAI\agno\.venv\Scripts\python.exe -m pytest tests/test_basic.py -v

# Run with coverage
C:\Users\tyler\dev\PyScrAI\agno\.venv\Scripts\python.exe -m pytest tests/ --cov=pyscrai
```

## Test Features

- **In-memory SQLite database** for isolated testing
- **Async test support** for engine testing
- **Clean fixtures** that don't interfere with each other
- **Simple mocks** and test doubles where needed

## Adding New Tests

1. Create new test files with `test_*.py` naming convention
2. Import required fixtures from `conftest.py`
3. Use `@pytest.mark.asyncio` for async tests
4. Follow the existing patterns for consistency
