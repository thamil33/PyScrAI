import asyncio

from agno.agent import Agent
from agno.models.cerebras import CerebrasOpenAI

agent = Agent(
    model=CerebrasOpenAI(id="llama-4-scout-17b-16e-instruct"),
    show_tool_calls=True,
    markdown=True,
    debug_mode=True,
)

# Print the response in the terminal
asyncio.run(agent.aprint_response("write a two sentence horror story", stream=True))
