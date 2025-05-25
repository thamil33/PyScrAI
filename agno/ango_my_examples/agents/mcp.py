# filepath: c:\Users\tyler\dev\agno\agent.py
from dotenv import load_dotenv
import asyncio
import os
from typing import Iterator, AsyncIterator, List, Union
from pathlib import Path
from textwrap import dedent
from agno.agent import Agent, RunResponse
from agno.models.openrouter import OpenRouter 
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.utils.pprint import pprint_run_response
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.website import WebsiteKnowledgeBase
from agno.embedder.sentence_transformer import SentenceTransformerEmbedder
from sentence_transformers import SentenceTransformer

load_dotenv(".env")

# Create Website knowledge base
website_knowledge = WebsiteKnowledgeBase(
    urls=["https://docs.agno.com/introduction"],
    max_links=10,
    vector_db=ChromaDb(collection="sites", embedder=SentenceTransformer("all-MiniLM-L6-v2", model_kwargs={"torch_dtype": "bfloat16"}), reranker="", path='vector_db', persist=True)
)
# Define storage - using SQLite instead of ChromaDB for agent storage
# ChromaDB is better for vector embeddings, while SQLite is better for structured data
storage = SqliteStorage(db_file="data.db", table_name="agent_data")

# Create agent with knowledge base and storage
async def run_agent(message: str) -> None:
    """Run the filesystem agent with the given message."""
    # Initialize the MCP server
    # file_path = str(Path(__file__).parent.parent.parent.parent.parent)
    file_path = str(Path(__file__))
    # Create a client session to connect to the MCP server
    async with MCPTools(
        f"npx -y @modelcontextprotocol/server-filesystem {file_path}"
    ) as mcp_file_tools:
        agent_mcp_filesys= Agent(
            name="System Clerk",
            model=OpenRouter(id="opengvlab/internvl3-14b:free"),
            storage = SqliteStorage(db_file="data.db", table_name="storage_system_clerk.db"),
            tools=[mcp_file_tools],
            instructions=dedent("""\
                You are a filesystem assistant. Help users explore files and directories.

                - Navigate the filesystem to answer questions
                - Use the list_allowed_directories tool to find directories that you can access
                - Provide clear context about files you examine
                - Use headings to organize your responses
                - Be concise and focus on relevant information\
            """),
            markdown=True,
            show_tool_calls=True,
        )

        # Run the agent
        await agent_mcp_filesys.aprint_response(message, stream=True)

if __name__ == "__main__":
    # Basic example - exploring project license
    asyncio.run(run_agent("Create a table of contents for this project"))

    # File content example
    asyncio.run(
        run_agent("Show me the content of README.md and explain what this project does")
    )