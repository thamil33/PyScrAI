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
from agno.tools.reasoning import ReasoningTools
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
st_model = SentenceTransformer(model_name, local_files_only=False) # Set local_files_only=False if download is needed
    # Pass the pre-initialized model to SentenceTransformerEmbedder
embedder = SentenceTransformerEmbedder(
        id=model_name,
        sentence_transformer_client=st_model)

#################  Knowledge Base  ##################
knowledge_base= UrlKnowledge(
    urls=["https://docs.agno.com/llms-full.txt"],
    vector_db=LanceDb(
        uri=str(tmp_dir.joinpath("lancedb")),
        table_name="agno_assist_knowledge",
        search_type=SearchType.hybrid,
        embedder=embedder,
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
    FileTools(base_dir=cwd.parent.parent), # Changed to workspace root c:\Users\tyler\dev\agent
    # MCPTools(f"fastmcp run mcp_server.py"), # Consider if MCPTools are needed for your tasks
    # Crawl4aiTools(max_length=None) # Consider if Crawl4aiTools are needed for web scraping tasks
    # ReasoningTools(add_instructions=True,add_few_shot=True)
    ]


# setting up model provider openrouter
model = OpenRouter(
    # id="google/gemini-2.5-flash-preview-05-20", # Example alternative
    id="meta-llama/llama-4-maverick:free", 
    # temperature=0.5, # Adjust temperature for creativity vs. factuality

    api_key=os.environ.get("OPENROUTER_API_KEY"),
)

# Setting up Ollama model provider (local)
model_local = LMStudio(id="llama-3.1-deephermes-r1-reasoning-8b-darkidol-instruct-1.2-uncensored")


# setting up the agent
agnos_agent = Agent(
    name="AgnoAssist",
    model=model,

    description=dedent("""\
    You are AgnoAssist, an AI specializing in the Agno Python framework. 
    Your primary goal is to assist developers by providing clear explanations, 
    generating working code examples, and guiding them in using Agno effectively.
    Always search your knowledge base before answering.
    When creating agents, use filesystem tools to manage files and directories."""),

    instructions=dedent("""\
    Your mission is to provide expert support for Agno developers.
    1.  **Analyze Request**:
        *   Determine if the request needs knowledge base search, agent creation, or both.
        *   Identify 1-3 key Agno-related search terms if a knowledge search is needed.
        *   If creating an Agno Agent, search the knowledge base for relevant concepts and example code.
        *   Utilize provided tools if tool use is indicated.

    2.  **Iterative Knowledge Search (Always perform this step first)**:
        *   Use `search_knowledge_base` for Agno concepts, code examples, and implementation details.
        *   Continue searching until sufficient information is gathered or search terms are exhausted.

    3.  **Code Generation (If an Agent is requested)**:
        *   Create complete, runnable Python code examples for Agno Agents.
        *   Include:
            *   All necessary imports and setup.
            *   Comprehensive comments explaining the code.
            *   Example queries to test the agent.
            *   Ensure all dependencies are implicitly clear or stated.
            *   Use Filesystem tools to create necessary files/directories in the workspace.
            *   Adhere to Python best practices, including type hints where appropriate."""),
    knowledge=knowledge_base,
    search_knowledge=True,
    storage=agent_storage,
    tools=tools,
    # reasoning=True,
    show_tool_calls=True,
    # read_chat_history=True,
    # add_history_to_messages=T
    # num_history_responses=2,
    markdown=True,
)

task = "Load the following file: 'C:\\Users\\tyler\\dev\\agent\\.util\\agno_assist\\agent_agno_docs copy.py', debug and optimize it and then save it as `C:\\Users\\tyler\\dev\\agent\\.util\\agno_assist\\agent_agno_docs_new.py`"
# main function to run the agent
if __name__ == "__main__":

    # Set to False after the knowledge base is created
    load_knowledge_base = True # Set to False after initial knowledge base loading to save time
    if load_knowledge_base:
        logger.info("Loading knowledge base...")
        knowledge_base.load()
        logger.info("Knowledge base loaded successfully")

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
        # Create a truncated version of the task for the prompt
        task_preview = task
        if len(task) > 50: # Truncate if task string is too long for the prompt
            task_preview = task[:47] + "..."

        
        prompt_message = f"\nAgnoAssist ({task_preview if task else 'New Task'}): "
        # Get user input from CLI
        user_input = input(prompt_message)
        if not user_input.strip() and task: # If user just presses enter, use the predefined task
            user_input = task
            print(f"Running predefined task: {task}")
            task = "" # Clear the task after using it once
        
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