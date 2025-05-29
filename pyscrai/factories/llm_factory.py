"""
Native LLM Factory for PyScrAI.
Creates LLM instances using PyScrAI's native implementations without external dependencies.
"""
from typing import Optional, Any, Dict

from pyscrai.llm import BaseLLM, OpenRouterLLM, LMStudioLLM, MockLLM
from pyscrai.utils.config import settings


def get_llm_instance(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    **kwargs: Any
) -> BaseLLM:
    """
    Factory function to get a configured native LLM instance.
    Uses PyScrAI's central configuration from settings.

    Args:
        provider (Optional[str]): Override the default provider (e.g., "openrouter", "lmstudio", "mock").
                                  If None, uses PYSCRAI_DEFAULT_PROVIDER from settings.
        model_id (Optional[str]): Override the default model ID for the selected provider.
                                   If None, uses the default model ID for that provider from settings.
        **kwargs: Additional keyword arguments to pass to the LLM class constructor.
                  This can include parameters like 'temperature', 'max_tokens', etc.

    Returns:
        An instance of a native PyScrAI LLM class (OpenRouterLLM, LMStudioLLM, or MockLLM).

    Raises:
        ValueError: If the specified or default provider is unsupported.
    """
    active_provider = provider or settings.PYSCRAI_DEFAULT_PROVIDER

    if active_provider.lower() == "openrouter":
        active_model_id = model_id or settings.PYSCRAI_OPENROUTER_MODEL_ID
        
        return OpenRouterLLM(
            model_id=active_model_id,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            site_url=settings.OPENROUTER_SITE_URL,
            app_name=settings.OPENROUTER_X_TITLE,
            **kwargs
        )

    elif active_provider.lower() == "lmstudio":
        active_model_id = model_id or settings.PYSCRAI_LMSTUDIO_MODEL_ID
        
        return LMStudioLLM(
            model_id=active_model_id,
            api_key=settings.LMSTUDIO_API_KEY,
            base_url=settings.PYSCRAI_LMSTUDIO_API_BASE,
            **kwargs
        )
    
    elif active_provider.lower() == "mock":
        active_model_id = model_id or "mock-model"
        
        return MockLLM(
            model_id=active_model_id,
            **kwargs
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {active_provider}")


# Backward compatibility alias
get_agno_llm_instance = get_llm_instance


# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_llm_factory():
        """Test the LLM factory with different providers."""
        print(f"Default provider from settings: {settings.PYSCRAI_DEFAULT_PROVIDER}")

        # Test default provider
        try:
            default_llm = get_llm_instance(temperature=0.7)
            print(f"Successfully created LLM instance for default provider ({settings.PYSCRAI_DEFAULT_PROVIDER}): {type(default_llm)}")
            print(f"Model ID: {default_llm.model_id}")
            
            # Test generation
            response = await default_llm.agenerate("Hello, how are you?")
            print(f"Response: {response[:100]}...")
            
        except Exception as e:
            print(f"Error creating default LLM instance: {e}")

        # Test OpenRouter explicitly
        try:
            or_llm = get_llm_instance(
                provider="openrouter", 
                model_id="openai/gpt-4o-mini", 
                temperature=0.5
            )
            print(f"Successfully created LLM instance for OpenRouter: {type(or_llm)}")
            print(f"Model ID: {or_llm.model_id}")
        except Exception as e:
            print(f"Error creating OpenRouter LLM instance: {e}")

        # Test LMStudio explicitly
        try:
            lm_llm = get_llm_instance(
                provider="lmstudio", 
                model_id="Meta-Llama-3-8B-Instruct-GGUF/Meta-Llama-3-8B-Instruct-Q4_K_M.gguf", 
                temperature=0.6
            )
            print(f"Successfully created LLM instance for LMStudio: {type(lm_llm)}")
            print(f"Model ID: {lm_llm.model_id}")
        except Exception as e:
            print(f"Error creating LMStudio LLM instance: {e}")

        # Test Mock LLM
        try:
            mock_llm = get_llm_instance(provider="mock", temperature=0.8)
            print(f"Successfully created Mock LLM instance: {type(mock_llm)}")
            print(f"Model ID: {mock_llm.model_id}")
            
            # Test mock generation
            mock_response = await mock_llm.agenerate("Test prompt for mock LLM")
            print(f"Mock response: {mock_response}")
            
        except Exception as e:
            print(f"Error creating Mock LLM instance: {e}")

    # Run the test
    asyncio.run(test_llm_factory())
