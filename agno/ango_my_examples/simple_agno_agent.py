from agno.agent import Agent
from agno.tools.api import CustomApiTools
from agno.models.lmstudio import LMStudio
from agno.models.openrouter import OpenRouter

"""
Args:
    base_url (Optional[str]): Base URL for API calls
    username (Optional[str]): Username for basic authentication
    password (Optional[str]): Password for basic authentication
    api_key (Optional[str]): API key for authentication
    headers (Optional[Dict[str, str]]): Default headers to include in requests
    verify_ssl (bool): Whether to verify SSL certificates
    timeout (int): Request timeout in seconds
"""
model_local = LMStudio(id="llama")
model_openrouter = OpenRouter( id="meta-llama/llama-4-maverick:free", )

agent = Agent(
    model=model_local,
    description="You are an API agent that utilizes the CustomApiTools to make API calls and return the results.",
    instructions="Make API calls to the specified endpoints and return the results.",
    tools=[CustomApiTools(base_url="https://dog.ceo/api", make_request=True)],
    show_tool_calls=True,
    markdown=True,
)

agent.print_response(
    'Make api calls to the following two different endpoints- /breeds/image/random and /breeds/list/all to get a random dog image and list of dog breeds respectively. Make sure that the method is "GET" for both the api calls.'
)
