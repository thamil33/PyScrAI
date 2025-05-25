from agno.agent import Agent
from agno.models.xai import xAI
from agno.tools.yfinance import YFinanceTools

agent = Agent(
    model=xAI(id="grok-3-mini-fast", reasoning_effort="high"),
    tools=[
        YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        )
    ],
    instructions="Use tables to display data.",
    show_tool_calls=True,
    markdown=True,
)
agent.print_response("Write a report comparing NVDA to TSLA", stream=True)
