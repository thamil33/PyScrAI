from llm_factory import get_agno_llm_instance

from typing import Optional, Any, Dict

# Import Agno's specific model classes
from agno.models.openrouter import OpenRouter as AgnoOpenRouter
from agno.models.lmstudio import LMStudio as AgnoLMStudio
# Import the global settings instance from your config.py
from utils.config import settings

# Example usage (for testing this factory function directly):

if __name__ == "__main__":
    # Ensure your .env file is in the root or environment variables are set
    print(f"Default provider from settings: {settings.PYSCRAI_DEFAULT_PROVIDER}")

    # Test default provider
    try:
        default_llm = get_agno_llm_instance(temperature=0.7)
        print(f"Successfully created LLM instance for default provider ({settings.PYSCRAI_DEFAULT_PROVIDER}): {type(default_llm)}")
        print(f"Model ID: {default_llm.id}") # Assuming Agno models have an 'id' attribute
    except Exception as e:
        print(f"Error creating default LLM instance: {e}")

    # Test OpenRouter explicitly
    try:
        or_llm = get_agno_llm_instance(provider="openrouter", model_id="openai/gpt-4o-mini", temperature=0.5)
        print(f"Successfully created LLM instance for OpenRouter: {type(or_llm)}")
        print(f"Model ID: {or_llm.id}")
    except Exception as e:
        print(f"Error creating OpenRouter LLM instance: {e}")

    # Test LMStudio explicitly
    try:
        lm_llm = get_agno_llm_instance(provider="lmstudio", model_id="Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf", temperature=0.6)
        print(f"Successfully created LLM instance for LMStudio: {type(lm_llm)}")
        print(f"Model ID: {lm_llm.id}")
    except Exception as e:
        print(f"Error creating LMStudio LLM instance: {e}")
