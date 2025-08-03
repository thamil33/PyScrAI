"""
Setup configuration for the LangGraph Multi-Agent Simulation Framework.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#')
        ]
else:
    requirements = []

setup(
    name="langgraph-multi-agent-simulation",
    version="0.1.0",
    author="LangGraph Multi-Agent Simulation Framework Team",
    author_email="",
    description="A flexible framework for creating and orchestrating multi-agent simulations using LangGraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/langgraph-multi-agent-simulation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "ruff>=0.1.0",
            "pre-commit>=3.5.0",
            "mypy>=1.7.0",
            "types-requests>=2.31.0",
        ],
        "testing": [
            "hypothesis>=6.88.0",
            "pytest-cov>=4.1.0",
        ],
        "web": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "simulation-framework=simulation_framework.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "simulation_framework": [
            "*.md",
            "*.txt",
            "*.yaml",
            "*.yml",
        ],
    },
    zip_safe=False,
    keywords=[
        "ai",
        "multi-agent",
        "simulation",
        "langgraph",
        "langchain",
        "llm",
        "agents",
        "workflow",
        "orchestration",
    ],
    project_urls={
        "Bug Reports": "https://github.com/your-org/langgraph-multi-agent-simulation/issues",
        "Source": "https://github.com/your-org/langgraph-multi-agent-simulation",
        "Documentation": "https://your-org.github.io/langgraph-multi-agent-simulation/",
    },
)
