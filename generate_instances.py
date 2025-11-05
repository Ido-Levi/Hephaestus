#!/usr/bin/env python3
"""
Generate instances.yaml for SWEBench-Verified benchmark runs.

This script fetches the SWEBench-Verified dataset and creates an instances.yaml
file with N uncompleted instances, excluding any already processed in swebench_results/.

Usage:
    python generate_instances.py --count 10
    python generate_instances.py --count 20 --output my_instances.yaml
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Set

import yaml

try:
    from datasets import load_dataset
except ImportError:
    print("ERROR: 'datasets' library not found.")
    print("Please install it with: pip install datasets")
    sys.exit(1)


def get_completed_instances(results_dir: Path) -> Set[str]:
    """Get list of instance IDs that have already been completed.

    Args:
        results_dir: Path to swebench_results directory

    Returns:
        Set of completed instance IDs
    """
    if not results_dir.exists():
        print(f"[Info] Results directory not found: {results_dir}")
        print("[Info] Assuming no instances have been completed yet")
        return set()

    # Each completed instance has its own directory
    completed = set()
    for item in results_dir.iterdir():
        if item.is_dir():
            completed.add(item.name)

    print(f"[Info] Found {len(completed)} completed instances in {results_dir}")
    return completed


def fetch_swebench_verified_instances(fast_eval: bool = False) -> List[str]:
    """Fetch all instance IDs from SWEBench-Verified dataset.

    Args:
        fast_eval: If True, only return instances with difficulty '<15 min fix'

    Returns:
        List of instance IDs
    """
    print("[Info] Fetching SWEBench-Verified dataset from HuggingFace...")
    print("[Info] This may take a moment on first run (dataset will be cached)")

    try:
        # Load the SWEBench-Verified dataset
        dataset = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")

        # Filter by difficulty if fast_eval mode is enabled
        if fast_eval:
            print("[Info] Fast-eval mode: filtering for '<15 min fix' instances only")
            instance_ids = [
                item["instance_id"] for item in dataset
                if item.get("difficulty") == "<15 min fix"
            ]
            print(f"[Info] Found {len(instance_ids)} fast instances (difficulty: '<15 min fix')")
        else:
            # Extract all instance IDs
            instance_ids = [item["instance_id"] for item in dataset]
            print(f"[Info] Successfully loaded {len(instance_ids)} instances from SWEBench-Verified")

        return instance_ids

    except Exception as e:
        print(f"[Error] Failed to load SWEBench-Verified dataset: {e}")
        print("[Error] Make sure you have internet connection and 'datasets' library installed")
        sys.exit(1)


def generate_instances_yaml(
    count: int,
    output_file: Path,
    results_dir: Path,
    fast_eval: bool = False
) -> None:
    """Generate instances.yaml with N uncompleted instances.

    Args:
        count: Number of instances to include
        output_file: Path to output YAML file
        results_dir: Path to swebench_results directory
        fast_eval: If True, only select instances with difficulty '<15 min fix'
    """
    # Get completed instances
    completed = get_completed_instances(results_dir)

    # Fetch all SWEBench-Verified instances
    all_instances = fetch_swebench_verified_instances(fast_eval=fast_eval)

    # Filter out completed instances
    available_instances = [
        instance_id for instance_id in all_instances
        if instance_id not in completed
    ]

    print(f"\n[Info] Total instances in SWEBench-Verified: {len(all_instances)}")
    print(f"[Info] Already completed: {len(completed)}")
    print(f"[Info] Available to run: {len(available_instances)}")

    if len(available_instances) == 0:
        print("\n[Success] All instances have been completed! 🎉")
        sys.exit(0)

    # Check if we have enough instances
    if count > len(available_instances):
        print(f"\n[Warning] Requested {count} instances, but only {len(available_instances)} are available")
        print(f"[Warning] Using all {len(available_instances)} available instances")
        count = len(available_instances)

    # Randomly select N available instances
    selected_instances = random.sample(available_instances, count)

    # Create YAML structure
    yaml_data = {
        "instances": selected_instances
    }

    # Write to file
    with open(output_file, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

    print(f"\n[Success] Created {output_file} with {len(selected_instances)} instances:")
    print(f"[Success] File location: {output_file.absolute()}")
    print(f"\n[Info] Selected instances:")
    for i, instance_id in enumerate(selected_instances, 1):
        print(f"  {i}. {instance_id}")

    print(f"\n[Next Steps] Run the benchmark with:")
    print(f"  python run_swebench_batch.py \\")
    print(f"      --instances {output_file} \\")
    print(f"      --timeout 3000 \\")
    print(f"      --poll-interval 30")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate instances.yaml for SWEBench-Verified benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 10 instances
  python generate_instances.py --count 10

  # Generate 20 instances with custom output filename
  python generate_instances.py --count 20 --output my_batch.yaml

  # Generate 5 instances, specifying custom results directory
  python generate_instances.py --count 5 --results-dir ./custom_results

  # Generate 10 fast-eval instances (difficulty: '<15 min fix')
  python generate_instances.py --count 10 --fast-eval
        """
    )

    parser.add_argument(
        "--count",
        type=int,
        required=True,
        help="Number of instances to generate"
    )

    parser.add_argument(
        "--output",
        default="instances.yaml",
        help="Output YAML filename (default: instances.yaml)"
    )

    parser.add_argument(
        "--results-dir",
        default="./swebench_results",
        help="Path to results directory (default: ./swebench_results)"
    )

    parser.add_argument(
        "--fast-eval",
        action="store_true",
        help="Only select instances with difficulty '<15 min fix' for faster evaluation"
    )

    args = parser.parse_args()

    # Validate count
    if args.count <= 0:
        print(f"[Error] Count must be positive (got {args.count})")
        sys.exit(1)

    # Convert paths
    output_file = Path(args.output)
    results_dir = Path(args.results_dir)

    # Check if output file already exists
    if output_file.exists():
        response = input(f"\n[Warning] {output_file} already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("[Info] Cancelled")
            sys.exit(0)

    print(f"\n{'='*70}")
    print(f"SWEBENCH INSTANCE GENERATOR")
    print(f"{'='*70}\n")

    # Generate the instances file
    generate_instances_yaml(
        count=args.count,
        output_file=output_file,
        results_dir=results_dir,
        fast_eval=args.fast_eval
    )


if __name__ == "__main__":
    main()
