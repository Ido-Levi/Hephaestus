#!/usr/bin/env python3
"""Inspect Qdrant collections and record counts."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.memory.vector_store import VectorStoreManager


def main():
    print("Connecting to Qdrant at http://localhost:6333...")
    print()

    # Initialize the vector store manager
    vector_store = VectorStoreManager(
        qdrant_url="http://localhost:6333",
        collection_prefix="hephaestus"
    )

    # Get statistics for all collections
    stats = vector_store.get_all_stats()

    print("=" * 70)
    print(f"{'Collection Name':<30} {'Records':<15} {'Status':<10}")
    print("=" * 70)

    total_records = 0
    for collection_name, collection_stats in stats.items():
        full_name = f"hephaestus_{collection_name}"
        record_count = collection_stats.get("vectors_count", 0)
        status = collection_stats.get("status", "unknown")

        print(f"{full_name:<30} {record_count:<15} {status:<10}")
        total_records += record_count

    print("=" * 70)
    print(f"{'TOTAL':<30} {total_records:<15}")
    print("=" * 70)
    print()

    # Show collection descriptions
    print("Collection Descriptions:")
    print("-" * 70)
    for collection_name, config in VectorStoreManager.COLLECTIONS.items():
        print(f"  • {collection_name}: {config['description']}")
    print()


if __name__ == "__main__":
    main()
