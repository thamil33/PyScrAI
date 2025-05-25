import os
import logging
from pathlib import Path
from textwrap import dedent
from dotenv import load_dotenv

# Agno framework imports
from agno.agent import Agent
from agno.utils.log import logger
from agno.tools.file import FileTools
from agno.tools.mcp import MCPTools
from agno.models.openrouter import OpenRouter
from agno.models.lmstudio import LMStudio
from agno.storage.sqlite import SqliteStorage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger.info("Starting MCP-NPM Agent")

# Setup paths
cwd = Path(__file__).parent
tmp_dir = cwd.joinpath("data")
tmp_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Working directory: {cwd}")
logger.info(f"Data directory: {tmp_dir}")

# Setting up agent storage
agent_storage = SqliteStorage(
    table_name="mcp_npm_agent_sessions",
    db_file=str(tmp_dir.joinpath("mcp_npm_sessions.db")),
)

# Setting up agent tools
# The MCPTools will use npx to temporarily install and run MCP servers
tools = [
    FileTools(base_dir=Path(r'C:\Users\tyler\dev\agent\.util')),
    # Use npx to run an MCP server without permanent installation
MCPTools(command="npx -y @fastmcp/cli run mcp_server.js", port=8000),
MCPTools(command="npx -y @mcp-plugins/web-search", port=8001),
MCPTools(command="npx -y @mcp/code-interpreter run", port=8002),
    # Alternative using npm (uncomment if preferred)
    # MCPTools(command="npm exec --yes -- @fastmcp/cli run mcp_server.js"),
]

# Setting up model providers
# Remote model via OpenRouter
model_remote = OpenRouter(
    id="mistralai/mistral-small-3.1-24b-instruct:free", 
    temperature=0.2,
    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# Local model via LM Studio
model_local = LMStudio(id="darkidol-llama-3.1-8b-instruct-1.2-uncensored-iq-imatrix-request@q6_k")

# Setting up the agent with MCP capabilities
mcp_agent = Agent(
    name="MCPAgent",
    model=model_local,  # Use local model by default (change to model_remote if needed)
    description=dedent("""\
    You are MCPAgent, an AI assistant powered by Agno framework with MCP (Model Control Protocol) 
    capabilities. You can communicate with JavaScript-based MCP servers that are launched on-demand 
    using npm/npx commands."""),
    
    instructions=dedent("""\
    Your primary function is to demonstrate the capabilities of MCP Tools in Agno:
    
    1. You can use MCP servers to extend your capabilities via JavaScript functionality
    2. When asked about specific tasks, use the appropriate MCP tools to accomplish them
    3. Explain how the MCP integration works when providing solutions
    4. Recommend best practices for MCP server implementation
    
    When using MCP tools:
    - The MCP server is started using npx, which temporarily installs the necessary packages
    - You can communicate with the server via JSON messages
    - You can execute JavaScript code through the MCP server
    - Remember to handle errors gracefully
    """),
    
    storage=agent_storage,
    tools=tools,
    show_tool_calls=True,
    read_chat_history=True,
    add_history_to_messages=True,
    num_history_responses=2,
    markdown=True,
)

# Main function to run the agent
if __name__ == "__main__":
    print("\n===== MCP-NPM Agent Interactive CLI =====")
    print("Type your questions or commands below.")
    print("Type 'exit', 'quit', or 'q' to exit.")
    
    logger.info("MCP-NPM Agent Interactive CLI started")
    while True:
        # Get user input from CLI
        user_input = input("\n> ")
        
        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Exiting MCP-NPM Agent. Goodbye!")
            break
        
        # Process the user's input through the agent
        if user_input.strip():
            try:
                logger.debug(f"Processing user input: {user_input}")
                mcp_agent.print_response(user_input, stream=True)
            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                print(f"Error: {e}")
                print("An error occurred while processing your request.")