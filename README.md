# PyScrAI - AI-Powered Scenario Simulation Platform

PyScrAI is an advanced AI-powered platform for creating, managing, and executing multi-agent scenario simulations.

## Project Structure

```
pyscrai/           # Core application code
├── databases/     # Database models and API
├── engines/       # AI processing engines
├── factories/     # Object creation factories
├── templates/     # Agent and scenario templates
└── utils/         # Utility modules

tests/             # Test suite
├── setup_scripts/ # Test setup and database initialization
└── test_*.py      # Test files

docs/              # Documentation
└── Project_Documentation/ # Core project docs
```

## Development Setup

1. **Virtual Environment**: `C:\Users\tyler\dev\PyScrAI\agno\.venv\Scripts\python.exe`
2. **Package Manager**: UV (pyproject.toml)
3. **Python Version**: 3.12.7
4. **Shell**: PowerShell

## For GitHub Copilot Users

**IMPORTANT**: When working with Copilot Chat, always exclude these directories:
- `agno/` - External Agno framework (not part of PyScrAI)
- `docs/Agno&OpenRouter_FullDocs/` - External documentation

**Focus searches on**:
- `pyscrai/**/*.py` - Core application code
- `tests/**/*.py` - Test files
- `docs/Project_Documentation/**` - Project documentation

Use this prompt template with Copilot Chat:
```
Working on PyScrAI. Exclude agno/ and docs/Agno&OpenRouter_FullDocs/ directories. Focus on pyscrai/, tests/, and docs/Project_Documentation/ only. [Your question]
```

## Getting Started

1. Activate virtual environment
2. Run database setup: `python tests/setup_scripts/setup_database.py --setup`
3. Run tests: `pytest tests/`

## Documentation

- [Development Plan](docs/development_notes/Current_Development_Plan.md)
- [Database Architecture](docs/Project_Documentation/database_architecture.md)
- [Engine API](docs/Project_Documentation/engine_api.md)
