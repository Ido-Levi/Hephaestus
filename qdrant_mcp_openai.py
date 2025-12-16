#!/usr/bin/env python3
"""Custom Qdrant MCP server using configured embedding provider.

This MCP server wraps Qdrant with embeddings from the configured provider
(OpenAI, Google AI, Azure, etc.) based on hephaestus_config.yaml.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from fastmcp import FastMCP

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.core.simple_config import get_config

# Initialize FastMCP
mcp = FastMCP("Qdrant with Configured Embeddings")

# Load configuration using Hephaestus config system
config = get_config()

# Extract configuration
embedding_provider = getattr(config, 'embedding_provider', 'openai')
embedding_model = config.embedding_model
QDRANT_URL = os.getenv("QDRANT_URL") or config.qdrant_url
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "hephaestus_agent_memories")

# Initialize Qdrant client
qdrant_client = QdrantClient(url=QDRANT_URL)

# Initialize embedding client based on provider
embedding_client = None

if embedding_provider == 'openai':
    from langchain_openai import OpenAIEmbeddings
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    embedding_client = OpenAIEmbeddings(
        model=embedding_model,
        openai_api_key=api_key
    )
    
elif embedding_provider == 'google_ai':
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    embedding_client = GoogleGenerativeAIEmbeddings(
        model=embedding_model,
        google_api_key=api_key
    )
    
elif embedding_provider == 'azure_openai':
    from langchain_openai import AzureOpenAIEmbeddings
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    if not api_key or not endpoint:
        print("Error: AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT required", file=sys.stderr)
        sys.exit(1)
    embedding_client = AzureOpenAIEmbeddings(
        model=embedding_model,
        azure_deployment=embedding_model,
        azure_endpoint=endpoint,
        api_key=api_key
    )
else:
    print(f"Error: Unsupported embedding provider: {embedding_provider}", file=sys.stderr)
    sys.exit(1)


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding using configured provider."""
    try:
        embedding = await embedding_client.aembed_query(text[:8000])
        return embedding
    except Exception as e:
        raise Exception(f"Failed to generate embedding: {e}")


@mcp.tool()
async def qdrant_find(query: str, limit: int = 5) -> str:
    """Search for relevant information in Qdrant using semantic search.

    Args:
        query: Natural language search query
        limit: Maximum number of results to return (default: 5)

    Returns:
        JSON string with search results containing relevant memories
    """
    try:
        # Generate embedding for query
        query_embedding = await generate_embedding(query)

        # Search Qdrant using query_points (new API)
        results = qdrant_client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=limit,
            with_payload=True,
        ).points

        # Format results
        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append({
                "rank": i,
                "score": round(result.score, 4),
                "content": result.payload.get("content", ""),
                "memory_type": result.payload.get("memory_type", "unknown"),
                "agent_id": result.payload.get("agent_id", "unknown"),
                "timestamp": result.payload.get("timestamp", ""),
            })

        if not formatted_results:
            return "No relevant memories found for your query."

        # Format as readable text
        output = f"Found {len(formatted_results)} relevant memories:\n\n"
        for r in formatted_results:
            output += f"[{r['rank']}] Score: {r['score']} | Type: {r['memory_type']}\n"
            output += f"    {r['content']}\n"
            output += f"    (Agent: {r['agent_id'][:8]}... | {r['timestamp'][:10]})\n\n"

        return output

    except Exception as e:
        return f"Error searching Qdrant: {str(e)}"


@mcp.tool()
async def qdrant_store(content: str, metadata: Dict[str, Any] = None) -> str:
    """Store information in Qdrant.

    Note: Agents should use the Hephaestus save_memory tool instead.
    This is provided for completeness but is not the recommended method.

    Args:
        content: Content to store
        metadata: Optional metadata dict

    Returns:
        Success message
    """
    return "Please use the Hephaestus 'save_memory' tool instead of qdrant_store for consistency."


if __name__ == "__main__":
    print(f"Starting Qdrant MCP server with {embedding_provider} embeddings", file=sys.stderr)
    print(f"  Provider: {embedding_provider}", file=sys.stderr)
    print(f"  Model: {embedding_model}", file=sys.stderr)
    print(f"  Collection: {COLLECTION_NAME}", file=sys.stderr)
    print(f"  Qdrant: {QDRANT_URL}", file=sys.stderr)

    # Run MCP server
    mcp.run()