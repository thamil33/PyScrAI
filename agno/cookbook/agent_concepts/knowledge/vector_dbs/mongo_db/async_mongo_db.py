"""
1. Create a MongoDB Atlas Account:
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for a free account

2. Create a New Cluster:
   - Click "Build a Database"
   - Choose the FREE tier (M0)
   - Select your preferred cloud provider and region
   - Click "Create Cluster"

3. Set Up Database Access:
   - Follow the instructions in the MongoDB Atlas UI
   - Create a username and password
   - Click "Add New Database User"

5. Get Connection String:
   - Select "Drivers" as connection method
   - Select "Python" as driver
   - Copy the connection string

7. Test Connection:
   - Use the connection string in your code
   - Ensure pymongo is installed: pip install "pymongo[srv]"
   - Test with a simple query to verify connectivity

Alternatively to test locally, you can run a docker container

docker run -p 27017:27017 -d --name mongodb-container --rm -v ./tmp/mongo-data:/data/db mongodb/mongodb-atlas-local:8.0.3
"""

import asyncio

from agno.agent import Agent
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.mongodb import MongoDb

# MongoDB Atlas connection string
"""
Example connection strings:
"mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"
"mongodb://localhost:27017/agno?authSource=admin"
"""
mdb_connection_string = "mongodb+srv://<username>:<password>@cluster0.mongodb.net/?retryWrites=true&w=majority"

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=MongoDb(
        collection_name="recipes",
        db_url=mdb_connection_string,
    ),
)

# Create and use the agent
agent = Agent(knowledge=knowledge_base, show_tool_calls=True)

if __name__ == "__main__":
    # Comment out after the first run
    asyncio.run(knowledge_base.aload(recreate=False))

    asyncio.run(agent.aprint_response("How to make Thai curry?", markdown=True))
