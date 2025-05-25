# Standard library import
import logging
from pathlib import Path
# from re import DEBUG
from textwrap import dedent
import os
import subprocess

# Third-party imports
# from cohere import EmbedRequestTruncate
from sentence_transformers import SentenceTransformer

# Add this import to fix the error:
from agno.embedder.sentence_transformer import SentenceTransformerEmbedder

# Agno framework imports
from agno.agent import Agent
from agno.utils.log import logger 
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.url import UrlKnowledge
# from agno.tools.crawl4ai import Crawl4aiTools
from agno.storage.sqlite import SqliteStorage
from agno.tools.file import FileTools
# from agno.tools.mcp import MCPTools
from agno.vectordb.lancedb import LanceDb, SearchType
#  Agno Models imports
from agno.models.openrouter import OpenRouter
from agno.models.ollama import Ollama
from agno.models.lmstudio import LMStudio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure Agno logger instead of using basic logging
logging.basicConfig(level=logging.INFO)  # Set to DEBUG for detailed logging
logger.info("Starting AgnoAssist application")

# Setup paths
cwd = Path(__file__).parent
tmp_dir = cwd.joinpath("data")
tmp_dir.mkdir(parents=True, exist_ok=True)
logger.info(f"Working directory: {cwd}")
logger.info(f"Data directory: {tmp_dir}")

# Setting up local Ollama text embedding model 
# embedder = OllamaEmbedder(id='nomic-embed-text', dimensions=768)
model_name = "multi-qa-distilbert-cos-v1"
    # Initialize SentenceTransformer with local_files_only=True
st_model = SentenceTransformer(model_name, local_files_only=False)
    # Pass the pre-initialized model to SentenceTransformerEmbedder
embedder = SentenceTransformerEmbedder(
        id=model_name,
        sentence_transformer_client=st_model)

#################  Knowledge Base  ##################
agno_kb= UrlKnowledge(
    urls=["https://docs.agno.com/llms-full.txt"],
    vector_db=LanceDb(
        uri=str(tmp_dir.joinpath("lancedb")),
        table_name="agno_assist_knowledge",
        embedder=embedder,
    ),
)

yt_dlp_kb = UrlKnowledge(
    urls=["https://raw.githubusercontent.com/yt-dlp/yt-dlp/refs/heads/master/README.md"],
    vector_db=LanceDb(
        uri=str(tmp_dir.joinpath("lancedb")),
        table_name="yt-dlp_assist_kb",
        embedder=embedder,
    ),
)
# openrouter_kb = UrlKnowledge(
#     urls=["https://openrouter.ai/docs/llms-full.txt"],
#     vector_db=LanceDb(
#         uri=str(tmp_dir.joinpath("lancedb")),
#         table_name="openrouter_assist_knowledge",
#         embedder=embedder,
#     ),
# )
# Combine knowledge bases
knowledge_base = CombinedKnowledgeBase(
    sources=[
        agno_kb,
        yt_dlp_kb,        
    ],
    # Use the same vector database for all knowledge bases
    vector_db=LanceDb(
        uri=str(tmp_dir.joinpath("lancedb")),
        table_name="combined_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=embedder
    ),
)
################# /Knowledge Base  ##################


# Setting up the agent storage with sqlite db
agent_storage = SqliteStorage(
    table_name="agno_assist_sessions",
    db_file=str(tmp_dir.joinpath("agent_sessions.db")),
)

# setting up agent tools 
tools = [
    FileTools(base_dir=Path(r'C:\Users\tyler\dev\agent\.util')),
    # MCPTools(f"fastmcp run mcp_server.py"),
    # Crawl4aiTools(max_length=None)
    ]


# setting up model provider openrouter
model = OpenRouter(
    # id="google/gemini-2.0-flash-001",
    id="mistralai/mistral-small-3.1-24b-instruct:free", 
    temperature=0.2,

    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# Setting up Ollama model provider (local)
model_local = LMStudio(id="darkidol-llama-3.1-8b-instruct-1.2-uncensored-iq-imatrix-request@q6_k")





# setting up the agent
agnos_agent = Agent(
    name="AgnoAssist",
    model=model_local,

    description=dedent("""\
    You are AgnoAssist, an AI Agent specializing in Agno: A lightweight python framework for building multimodal agents.
    Your goal is to help developers understand and effectively use Agno by providing
    explanations and working code examples"""),

    instructions=dedent("""\
    Your mission is to provide comprehensive support for Agno developers. Follow these steps to ensure the best possible response:

    1. **Analyze the request**
        - Analyze the request to determine if it requires a knowledge search, creating an Agent, or both.
        - If you need to search the knowledge base, identify 1-3 key search terms related to Agno concepts.
        - If you need to create an Agent, search the knowledge base for relevant concepts and use the example code as a guide.
        - When the user asks for an Agent, they mean an Agno Agent.
        - If tool use is required, use the tools provided. 

    After Analysis, always start the iterative search process. No need to wait for approval from the user.

    2. **Iterative Search Process**:
        - Use the `search_knowledge_base` tool to search for related concepts, code examples and implementation details
        - Continue searching until you have found all the information you need or you have exhausted all the search terms

    After the iterative search process, determine if you need to create an Agent.
    If you do, generate a code example that the user can run.

    3. **Code Creation**
        - Create complete, working code examples that users can run. For example:
        ```python
        from agno.agent import Agent
        from agno.tools.duckduckgo import DuckDuckGoTools

        agent = Agent(tools=[DuckDuckGoTools()])

        # Perform a web search and capture the response
        response = agent.run("What's happening in France?")
        ```
        - Remember to:
            * Build the complete agent implementation.
            * Include all necessary imports and setup.
            * Add comprehensive comments explaining the implementation
            * Test the agent with example queries
            * Ensure all dependencies are listed
            * Include error handling and best practices
            * Add type hints and documentation
                    
        Key topics to cover:
        - Agent levels and capabilities
        - Knowledge base and memory management
        - Tool integration
        - Model support and configuration
        - Best practices and common patterns
                            """),
    knowledge=knowledge_base,
    storage=agent_storage,
    tools=tools,
    show_tool_calls=True,
    # 1. Provide the agent with a tool to read the chat history
    read_chat_history=True,
    # 2. Automatically add the chat history to the messages sent to the model
    add_history_to_messages=True,
    # Number of historical runs to add to the messages.
    num_history_responses=2,
    markdown=True,
)


# main function to run the agent
if __name__ == "__main__":

    # Set to False after the knowledge base is created
    load_knowledge_base = True
    if load_knowledge_base:
        logger.info("Loading knowledge base...")
        agno_kb.load()
        logger.info("Knowledge base loaded successfully")

    print("\n===== AgnoAssist Interactive CLI =====")
    print("\n===== AgnoAssist Interactive CLI =====")
    print("Type your questions or commands below.")
    print(""" 
          
         T::    T::     :::      ::::    :::  ::::::::::: :::   :::::::::::: ::::::::  ::::    ::: 
         :+:    :+:   :+: :+:   +:+:+: :+:+:+     :+:     :+:        :+:    :+:    :+: :+:+:   :+: 
         +:+    +:+  +:+   +:+  +:+ +:+:+ +:+     +:+     +:+        +:+    +:+    +:+ :+:+:+  +:+ 
         +#++:++#++ +#++:++#++: +#+  +:+  +#+     +#+     +#+        +#+    +#+    +:+ +#+ +:+ +#+ 
         +#+    +#+ +#+     +#+ +#+       +#+     +#+     +#+        +#+    +#+    +#+ +#+  +#+#+# 
         #+#    #+# #+#     #+# #+#       #+#     #+#     #+#        #+#    #+#    #+# #+#   #+#+# 
         ###    ### ###     ### ###       ### ########### ########## ###     ########  ###    ####  
         
        """)
    
    logger.info("AgnoAssist Interactive CLI started")
    while True:
        # Get user input from CLI
        user_input = input("\n> ")
        
        # Check if user wants to exit
        if user_input.lower() in ["exit", "quit", "q"]:
            print("Exiting AgnoAssist. Goodbye!")
            break
        
        # Process the user's input through the agent
        if user_input.strip():
            try:
                logger.debug(f"Processing user input: {user_input}")
                agnos_agent.print_response(user_input, stream=True)
            except Exception as e:
                logger.error(f"Error processing request: {e}", exc_info=True)
                print(f"Error: {e}")
                print("An error occurred while processing your request.")