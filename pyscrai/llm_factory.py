# PyScrAI/pyscrai/llm_factory.py
from typing import Optional, Any, Dict

# Import Agno's specific model classes
from agno_src.models.openrouter import OpenRouter as AgnoOpenRouter
from agno_src.models.lmstudio import LMStudio as AgnoLMStudio
# Import the global settings instance from your config.py
from pyscrai.utils.config import settings

def get_agno_llm_instance(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    **kwargs: Any
) -> Any: # Should ideally return Union[AgnoOpenRouter, AgnoLMStudio, ...] or a base Agno model type
    """
    Factory function to get a configured Agno LLM instance.
    Uses PyScrAI's central configuration from settings.

    Args:
        provider (Optional[str]): Override the default provider (e.g., "openrouter", "lmstudio").
                                  If None, uses PYSCRAI_DEFAULT_PROVIDER from settings.
        model_id (Optional[str]): Override the default model ID for the selected provider.
                                   If None, uses the default model ID for that provider from settings.
        **kwargs: Additional keyword arguments to pass to the Agno model class constructor.
                  This can include parameters like 'temperature', 'max_tokens', etc.
                  It can also include 'extra_headers' for OpenRouter.

    Returns:
        An instance of an Agno LLM model class (e.g., AgnoOpenRouter or AgnoLMStudio).

    Raises:
        ValueError: If the specified or default provider is unsupported.
    """
    active_provider = provider or settings.PYSCRAI_DEFAULT_PROVIDER

    if active_provider.lower() == "openrouter":
        active_model_id = model_id or settings.OPENROUTER_DEFAULT_MODEL_ID
        
        # Prepare extra headers for OpenRouter if site_url or x_title are set
        extra_headers: Dict[str, str] = kwargs.pop("extra_headers", {})
        if settings.OPENROUTER_SITE_URL and "HTTP-Referer" not in extra_headers :
            extra_headers["HTTP-Referer"] = settings.OPENROUTER_SITE_URL
        if settings.OPENROUTER_X_TITLE and "X-Title" not in extra_headers:
            extra_headers["X-Title"] = settings.OPENROUTER_X_TITLE
        
        # Agno's OpenRouter class might pick up OPENROUTER_API_KEY from env by default.
        # It primarily uses 'id' for model selection.
        # We pass api_key and base_url explicitly if the Agno class supports them,
        # otherwise, they should be picked up from environment variables by Agno.
        # Based on simple_agno_agent.py, it seems id is the main config.
        # OpenRouter docs also show that api_key and base_url can be passed to OpenAI compatible clients.
        return AgnoOpenRouter(
            id=active_model_id,
            api_key=settings.OPENROUTER_API_KEY, # Pass if AgnoOpenRouter constructor accepts it
            # OPENROUTER_BASE_URL is often set via an environment variable for OpenAI SDK compatibility,
            # or passed as `base_url` to an OpenAI client instance.
            # If AgnoOpenRouter takes it directly, it would be:
            # base_url=settings.OPENROUTER_BASE_URL, 
            extra_headers=extra_headers if extra_headers else None, # Pass only if not empty
            **kwargs
        )

    elif active_provider.lower() == "lmstudio":
        active_model_id = model_id or settings.LMSTUDIO_DEFAULT_MODEL_ID
        # Agno's LMStudio class, like OpenRouter, primarily uses 'id'.
        # API key is often not needed for local LMStudio.
        # The base_url is crucial.
        return AgnoLMStudio(
            id=active_model_id,
            api_key=settings.LMSTUDIO_API_KEY, # Pass if AgnoLMStudio constructor accepts it
            base_url=settings.LMSTUDIO_BASE_URL, # Pass if AgnoLMStudio constructor accepts it
            **kwargs
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {active_provider}")

# Example usage (for testing this factory function directly):
# if __name__ == "__main__":
#     # Ensure your .env file is in the root or environment variables are set
#     print(f"Default provider from settings: {settings.PYSCRAI_DEFAULT_PROVIDER}")
#
#     # Test default provider
#     try:
#         default_llm = get_agno_llm_instance(temperature=0.7)
#         print(f"Successfully created LLM instance for default provider ({settings.PYSCRAI_DEFAULT_PROVIDER}): {type(default_llm)}")
#         print(f"Model ID: {default_llm.id}") # Assuming Agno models have an 'id' attribute
#     except Exception as e:
#         print(f"Error creating default LLM instance: {e}")
#
#     # Test OpenRouter explicitly
#     try:
#         or_llm = get_agno_llm_instance(provider="openrouter", model_id="openai/gpt-4o-mini", temperature=0.5)
#         print(f"Successfully created LLM instance for OpenRouter: {type(or_llm)}")
#         print(f"Model ID: {or_llm.id}")
#     except Exception as e:
#         print(f"Error creating OpenRouter LLM instance: {e}")
#
#     # Test LMStudio explicitly
#     try:
#         lm_llm = get_agno_llm_instance(provider="lmstudio", model_id="Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf", temperature=0.6)
#         print(f"Successfully created LLM instance for LMStudio: {type(lm_llm)}")
#         print(f"Model ID: {lm_llm.id}")
#     except Exception as e:
#         print(f"Error creating LMStudio LLM instance: {e}")
