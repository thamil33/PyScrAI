"""
This cookbook shows how to use prompt caching with Agents using Anthropic models, to catch the system prompt passed to the model.

This can significantly reduce processing time and costs.
Use it when working with a static and large system prompt.

You can check more about prompt caching with Anthropic models here: https://docs.anthropic.com/en/docs/prompt-caching
"""

from pathlib import Path

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.utils.media import download_file

# Load an example large system message from S3. A large prompt like this would benefit from caching.
txt_path = Path(__file__).parent.joinpath("system_promt.txt")
download_file(
    "https://agno-public.s3.amazonaws.com/prompts/system_promt.txt",
    str(txt_path),
)
system_message = txt_path.read_text()

agent = Agent(
    model=Claude(
        id="claude-sonnet-4-20250514",
        cache_system_prompt=True,  # Activate prompt caching for Anthropic to cache the system prompt
    ),
    system_message=system_message,
    markdown=True,
)

# First run - this will create the cache
response = agent.run(
    "Explain the difference between REST and GraphQL APIs with examples"
)
print(
    f"First run cache creation input tokens = {response.metrics['cache_creation_input_tokens']}"
)  # type: ignore

# Second run - this will use the cached system prompt
response = agent.run(
    "What are the key principles of clean code and how do I apply them in Python?"
)
print(
    f"Second run cache read input tokens = {response.metrics['cache_read_input_tokens']}"
)  # type: ignore
