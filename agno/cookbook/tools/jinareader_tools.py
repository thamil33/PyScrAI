from agno.agent import Agent
from agno.tools.jina import JinaReaderTools

agent = Agent(tools=[JinaReaderTools()], show_tool_calls=True)
agent.print_response("Summarize: https://github.com/agno-agi")
