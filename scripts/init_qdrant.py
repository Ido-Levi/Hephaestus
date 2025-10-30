#!/usr/bin/env python3
"""Initialize Qdrant vector database collections for Hephaestus."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.memory.vector_store import VectorStoreManager


def main():
    """Initialize Qdrant with all required collections."""
    print("Initializing Qdrant vector database...")
    print("Make sure Qdrant is running at http://localhost:6333")
    print()

    try:
        # Initialize vector store manager
        vector_store = VectorStoreManager(
            qdrant_url="http://localhost:6333",
            collection_prefix="hephaestus"
        )

        print("Collections initialized successfully!")
        print()

        # Get and display statistics
        stats = vector_store.get_all_stats()
        print("Collection Statistics:")
        for collection_name, collection_stats in stats.items():
            print(f"  - {collection_name}:")
            print(f"      Vectors: {collection_stats.get('vectors_count', 0)}")
            print(f"      Status: {collection_stats.get('status', 'unknown')}")

    except Exception as e:
        print(f"Error initializing Qdrant: {e}")
        print("\nMake sure Qdrant is running. You can start it with:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        sys.exit(1)


if __name__ == "__main__":
    main()