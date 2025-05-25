import asyncio

from agno.agent import Agent, RunResponse  # noqa
from agno.models.meta import LlamaOpenAI

agent = Agent(
    model=LlamaOpenAI(id="Llama-4-Maverick-17B-128E-Instruct-FP8"),
    markdown=True,
    debug_mode=True,
)

# Get the response in a variable
# run: RunResponse = asyncio.run(agent.arun("Share a 2 sentence horror story"))
# print(run.content)

# Print the response in the terminal
asyncio.run(agent.aprint_response("Share a 2 sentence horror story"))
