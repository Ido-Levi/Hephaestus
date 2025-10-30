#!/usr/bin/env python3
"""Clean Qdrant vector database - removes all collections and data.

This script is useful when:
- Moving from an old project to a new one
- Starting fresh with a clean memory system
- Clearing out test data

WARNING: This will DELETE ALL memories stored in Qdrant!
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from src.memory.vector_store import VectorStoreManager


def confirm_deletion():
    """Ask user to confirm deletion."""
    print("=" * 70)
    print("⚠️  WARNING: QDRANT DATABASE CLEANUP")
    print("=" * 70)
    print()
    print("This will DELETE ALL collections and memories from Qdrant:")
    print("  - agent_memories")
    print("  - static_docs")
    print("  - task_completions")
    print("  - error_solutions")
    print("  - domain_knowledge")
    print("  - project_context")
    print()
    print("This action CANNOT be undone!")
    print()

    response = input("Type 'DELETE' to confirm deletion: ").strip()
    return response == "DELETE"


def clean_qdrant(qdrant_url: str = "http://localhost:6333", collection_prefix: str = "hephaestus"):
    """Clean all Qdrant collections.

    Args:
        qdrant_url: URL of Qdrant server
        collection_prefix: Collection prefix to clean
    """
    print()
    print("Connecting to Qdrant...")

    try:
        client = QdrantClient(url=qdrant_url)

        # Get all collections
        collections = client.get_collections()
        print(f"Found {len(collections.collections)} total collections")
        print()

        # Filter collections with our prefix
        hephaestus_collections = [
            coll for coll in collections.collections
            if coll.name.startswith(collection_prefix)
        ]

        if not hephaestus_collections:
            print(f"No collections found with prefix '{collection_prefix}'")
            print("Nothing to clean!")
            return

        print(f"Found {len(hephaestus_collections)} Hephaestus collections:")
        for coll in hephaestus_collections:
            count = client.count(collection_name=coll.name)
            print(f"  - {coll.name}: {count.count} vectors")
        print()

        # Delete each collection
        print("Deleting collections...")
        for coll in hephaestus_collections:
            print(f"  Deleting {coll.name}...", end=" ")
            client.delete_collection(collection_name=coll.name)
            print("✓")

        print()
        print("=" * 70)
        print("✅ Qdrant cleanup complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  1. Run 'python scripts/init_qdrant.py' to recreate collections")
        print("  2. Memories will be repopulated as agents work")
        print()

    except Exception as e:
        print(f"❌ Error cleaning Qdrant: {e}")
        print()
        print("Make sure Qdrant is running:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        sys.exit(1)


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Clean Qdrant vector database (deletes all collections and memories)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode (asks for confirmation)
  python scripts/clean_qdrant.py

  # Force mode (skips confirmation - DANGEROUS!)
  python scripts/clean_qdrant.py --force

  # Custom Qdrant URL
  python scripts/clean_qdrant.py --url http://localhost:6333

  # Custom collection prefix
  python scripts/clean_qdrant.py --prefix my_project
        """
    )

    parser.add_argument(
        "--url",
        default="http://localhost:6333",
        help="Qdrant server URL (default: http://localhost:6333)"
    )

    parser.add_argument(
        "--prefix",
        default="hephaestus",
        help="Collection prefix to clean (default: hephaestus)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt (DANGEROUS!)"
    )

    args = parser.parse_args()

    # Confirm deletion unless --force is used
    if not args.force:
        if not confirm_deletion():
            print()
            print("Cleanup cancelled.")
            print()
            sys.exit(0)
    else:
        print()
        print("⚠️  Running in FORCE mode - skipping confirmation")
        print()

    # Clean Qdrant
    clean_qdrant(
        qdrant_url=args.url,
        collection_prefix=args.prefix
    )


if __name__ == "__main__":
    main()