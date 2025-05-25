"""
Couchbase Vector DB Example
==========================

Setup Couchbase Cluster (Local via Docker):
-------------------------------------------
1. Run Couchbase locally:

   docker run -d --name couchbase-server \
     -p 8091-8096:8091-8096 \
     -p 11210:11210 \
     -e COUCHBASE_ADMINISTRATOR_USERNAME=Administrator \
     -e COUCHBASE_ADMINISTRATOR_PASSWORD=password \
     couchbase:latest

2. Access the Couchbase UI at: http://localhost:8091
   (Login with the username and password above)

3. Create a new cluster. You can select "Finish with defaults".

4. Create a bucket named 'recipe_bucket', a scope 'recipe_scope', and a collection 'recipes'.

Managed Couchbase (Capella):
----------------------------
- For a managed cluster, use Couchbase Capella: https://cloud.couchbase.com/
- Follow Capella's UI to create a database, bucket, scope, and collection as above.

Environment Variables (export before running):
----------------------------------------------
Create a shell script (e.g., set_couchbase_env.sh):

    export COUCHBASE_USER="Administrator"
    export COUCHBASE_PASSWORD="password"
    export COUCHBASE_CONNECTION_STRING="couchbase://localhost"
    export OPENAI_API_KEY="<your-openai-api-key>"

# For Capella, set COUCHBASE_CONNECTION_STRING to the Capella connection string.

Install couchbase-sdk:
----------------------
    pip install couchbase
"""

import asyncio
import os
import time

from agno.agent import Agent
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.pdf_url import PDFUrlKnowledgeBase
from agno.vectordb.couchbase import CouchbaseSearch
from couchbase.auth import PasswordAuthenticator
from couchbase.management.search import SearchIndex
from couchbase.options import ClusterOptions, KnownConfigProfiles

# Couchbase connection settings
username = os.getenv("COUCHBASE_USER")  # Replace with your username
password = os.getenv("COUCHBASE_PASSWORD")  # Replace with your password
connection_string = os.getenv("COUCHBASE_CONNECTION_STRING")

# Create cluster options with authentication
auth = PasswordAuthenticator(username, password)
cluster_options = ClusterOptions(auth)
cluster_options.apply_profile(KnownConfigProfiles.WanDevelopment)

# Define the vector search index
search_index = SearchIndex(
    name="vector_search",
    source_type="gocbcore",
    idx_type="fulltext-index",
    source_name="recipe_bucket",
    plan_params={"index_partitions": 1, "num_replicas": 0},
    params={
        "doc_config": {
            "docid_prefix_delim": "",
            "docid_regexp": "",
            "mode": "scope.collection.type_field",
            "type_field": "type",
        },
        "mapping": {
            "default_analyzer": "standard",
            "default_datetime_parser": "dateTimeOptional",
            "index_dynamic": True,
            "store_dynamic": True,
            "default_mapping": {"dynamic": True, "enabled": False},
            "types": {
                "recipe_scope.recipes": {
                    "dynamic": False,
                    "enabled": True,
                    "properties": {
                        "content": {
                            "enabled": True,
                            "fields": [
                                {
                                    "docvalues": True,
                                    "include_in_all": False,
                                    "include_term_vectors": False,
                                    "index": True,
                                    "name": "content",
                                    "store": True,
                                    "type": "text",
                                }
                            ],
                        },
                        "embedding": {
                            "enabled": True,
                            "dynamic": False,
                            "fields": [
                                {
                                    "vector_index_optimized_for": "recall",
                                    "docvalues": True,
                                    "dims": 3072,
                                    "include_in_all": False,
                                    "include_term_vectors": False,
                                    "index": True,
                                    "name": "embedding",
                                    "similarity": "dot_product",
                                    "store": True,
                                    "type": "vector",
                                }
                            ],
                        },
                        "meta": {
                            "dynamic": True,
                            "enabled": True,
                            "properties": {
                                "name": {
                                    "enabled": True,
                                    "fields": [
                                        {
                                            "docvalues": True,
                                            "include_in_all": False,
                                            "include_term_vectors": False,
                                            "index": True,
                                            "name": "name",
                                            "store": True,
                                            "analyzer": "keyword",
                                            "type": "text",
                                        }
                                    ],
                                }
                            },
                        },
                    },
                }
            },
        },
    },
)

knowledge_base = PDFUrlKnowledgeBase(
    urls=["https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=CouchbaseSearch(
        bucket_name="recipe_bucket",
        scope_name="recipe_scope",
        collection_name="recipes",
        couchbase_connection_string=connection_string,
        cluster_options=cluster_options,
        search_index=search_index,
        embedder=OpenAIEmbedder(
            id="text-embedding-3-large",
            dimensions=3072,
            api_key=os.getenv("OPENAI_API_KEY"),
        ),
        wait_until_index_ready=60,
        overwrite=True,
    ),
)

# Create and use the agent
agent = Agent(knowledge=knowledge_base, show_tool_calls=True)


async def run_agent():
    await knowledge_base.aload(recreate=True)
    time.sleep(5)  # wait for the vector index to be sync with kv
    await agent.aprint_response("How to make Thai curry?", markdown=True)


if __name__ == "__main__":
    # Comment out after the first run
    asyncio.run(run_agent())
