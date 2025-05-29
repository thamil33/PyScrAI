"""
PyScrAI LLM module.
Native LLM implementations without external dependencies.
"""

from pyscrai.llm.base_llm import BaseLLM, OpenRouterLLM, LMStudioLLM, MockLLM

__all__ = [
    "BaseLLM",
    "OpenRouterLLM", 
    "LMStudioLLM",
    "MockLLM"
]
