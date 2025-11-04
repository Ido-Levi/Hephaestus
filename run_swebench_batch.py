#!/usr/bin/env python3
"""
Run multiple SWEBench instances sequentially with automatic result collection.

This script:
1. Reads a list of instance IDs from a YAML file
2. Runs each workflow sequentially
3. Monitors for validated results via API polling
4. Collects solution patches and execution logs
5. Cleans up between runs (Qdrant + temp files)

Usage:
    python run_swebench_batch.py --instances instances.yaml
    python run_swebench_batch.py --instances instances.yaml --timeout 3600
"""

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import requests
import yaml
from qdrant_client import QdrantClient


class SWEBenchBatchRunner:
    """Manages sequential execution of SWEBench workflows."""

    def __init__(
        self,
        instances_file: str,
        api_url: str = "http://localhost:4000/api/results",
        qdrant_url: str = "http://localhost:6333",
        db_path: str = "./hephaestus.db",
        poll_interval: int = 60,
        timeout: int = 7200,  # 2 hours default
    ):
        self.instances_file = Path(instances_file)
        self.results_dir = Path("./swebench_results")
        self.api_url = api_url
        self.qdrant_url = qdrant_url
        self.db_path = Path(db_path)
        self.poll_interval = poll_interval
        self.timeout = timeout

        # Track statistics
        self.stats = {
            "total": 0,
            "completed": 0,
            "failed": 0,
            "timed_out": 0,
        }

        # Current workflow process
        self.current_process: Optional[subprocess.Popen] = None
        self.current_instance_id: Optional[str] = None

    def load_instances(self) -> List[str]:
        """Load instance IDs from YAML file."""
        print(f"[Setup] Loading instances from {self.instances_file}")

        if not self.instances_file.exists():
            raise FileNotFoundError(f"Instance file not found: {self.instances_file}")

        with open(self.instances_file, 'r') as f:
            data = yaml.safe_load(f)

        # Support both list format and dict format
        if isinstance(data, list):
            instances = data
        elif isinstance(data, dict) and 'instances' in data:
            instances = data['instances']
        else:
            raise ValueError("YAML file must contain a list of instance IDs or a dict with 'instances' key")

        print(f"[Setup] Loaded {len(instances)} instances")
        return instances

    def setup_directories(self):
        """Create necessary directories."""
        self.results_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Setup] Results directory: {self.results_dir}")
        print(f"[Setup] Workspaces: Unique temp folder per instance (preserved for inspection)")

    def start_workflow(self, instance_id: str, workspace_path: Path) -> subprocess.Popen:
        """Start a SWEBench workflow for the given instance.

        Args:
            instance_id: The instance identifier
            workspace_path: Unique workspace directory for this instance
        """
        print(f"\n{'='*70}")
        print(f"[Workflow] Starting: {instance_id}")
        print(f"[Workflow] Workspace: {workspace_path}")
        print(f"{'='*70}\n")

        cmd = [
            "python",
            "run_swebench_workflow.py",
            "--path", str(workspace_path),
            "--instance-id", instance_id,
            "--drop-db"
        ]

        print(f"[Command] {' '.join(cmd)}")

        # Start process
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        self.current_process = process
        self.current_instance_id = instance_id

        return process

    def poll_for_result(self, instance_id: str, start_time: float) -> Optional[Dict]:
        """Poll API for validated result created after start_time.

        Args:
            instance_id: The instance identifier (for logging)
            start_time: Unix timestamp when workflow started

        Returns:
            Dict with result data if validated result found, None otherwise
        """
        try:
            response = requests.get(self.api_url, timeout=5)
            response.raise_for_status()

            results = response.json()

            # Look for validated result created AFTER this workflow started
            for result in results:
                if result.get("status") == "validated":
                    # Check if result was created after workflow start
                    validated_at_str = result.get('validated_at')
                    if validated_at_str:
                        try:
                            # Parse ISO timestamp to unix timestamp
                            validated_at = datetime.fromisoformat(validated_at_str.replace('Z', '+00:00'))
                            validated_timestamp = validated_at.timestamp()

                            # Only accept results validated AFTER this workflow started
                            if validated_timestamp > start_time:
                                print(f"\n[Result] ✅ Found validated result!")
                                print(f"[Result] Result ID: {result['result_id']}")
                                print(f"[Result] Validated at: {validated_at_str}")
                                print(f"[Result] Workflow started at: {datetime.fromtimestamp(start_time).isoformat()}")
                                return result
                            else:
                                # This is a stale result from a previous run - ignore it
                                print(f"[Poll] Ignoring stale result {result['result_id']} (validated before workflow started)")
                        except Exception as e:
                            print(f"[Poll] Warning: Could not parse timestamp for result {result.get('result_id')}: {e}")
                            continue

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > self.timeout:
                print(f"\n[Timeout] ⏰ Workflow exceeded timeout of {self.timeout}s ({elapsed:.0f}s elapsed)")
                return None

            # Print status update
            remaining = self.timeout - elapsed
            print(f"[Poll] No validated result yet. Waiting {self.poll_interval}s... (timeout in {remaining:.0f}s)")

        except requests.RequestException as e:
            print(f"[Poll] Warning: Could not reach API: {e}")
        except Exception as e:
            print(f"[Poll] Error polling API: {e}")

        return None

    def collect_results(self, instance_id: str, result_data: Dict, start_time: float, end_time: float):
        """Collect solution.patch and hephaestus.db for the instance.

        Args:
            instance_id: The instance identifier
            result_data: Result data from API
            start_time: Workflow start timestamp
            end_time: Workflow end timestamp
        """
        print(f"\n[Collect] Collecting results for {instance_id}")

        # Calculate duration
        duration_seconds = end_time - start_time
        duration_minutes = duration_seconds / 60
        duration_hours = duration_seconds / 3600

        print(f"[Collect] Duration: {duration_seconds:.1f}s ({duration_minutes:.1f}m / {duration_hours:.2f}h)")

        # Create instance directory
        instance_dir = self.results_dir / instance_id
        instance_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Collect] Instance directory: {instance_dir}")

        # Find and copy solution.patch from extra_files
        extra_files = result_data.get("extra_files", [])
        solution_patch_path = None

        for file_path in extra_files:
            if "solution.patch" in file_path:
                solution_patch_path = Path(file_path)
                break

        if solution_patch_path and solution_patch_path.exists():
            dest_patch = instance_dir / "solution.patch"
            shutil.copy2(solution_patch_path, dest_patch)
            print(f"[Collect] ✓ Copied solution.patch")
            print(f"           From: {solution_patch_path}")
            print(f"           To: {dest_patch}")
        else:
            print(f"[Collect] ⚠️  Warning: solution.patch not found in extra_files")
            print(f"[Collect]    Extra files: {extra_files}")

        # Copy hephaestus.db
        if self.db_path.exists():
            dest_db = instance_dir / "hephaestus.db"
            shutil.copy2(self.db_path, dest_db)
            print(f"[Collect] ✓ Copied hephaestus.db")
            print(f"           From: {self.db_path}")
            print(f"           To: {dest_db}")
        else:
            print(f"[Collect] ⚠️  Warning: {self.db_path} not found")

        # Create metadata with timing information
        from datetime import datetime

        metadata = {
            "instance_id": instance_id,
            "start_time": datetime.fromtimestamp(start_time).isoformat(),
            "end_time": datetime.fromtimestamp(end_time).isoformat(),
            "duration_seconds": round(duration_seconds, 2),
            "duration_minutes": round(duration_minutes, 2),
            "duration_hours": round(duration_hours, 2),
            "status": "completed",
            "result_id": result_data.get("result_id"),
            "validated_at": result_data.get("validated_at"),
        }

        metadata_path = instance_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"[Collect] ✓ Saved timing metadata to {metadata_path}")

        # Save full result data as separate file
        result_metadata_path = instance_dir / "result_metadata.json"
        with open(result_metadata_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f"[Collect] ✓ Saved result metadata to {result_metadata_path}")

        print(f"[Collect] ✅ Results collected successfully")

    def stop_workflow(self):
        """Stop the current workflow process."""
        if self.current_process:
            print(f"\n[Cleanup] Stopping workflow process (PID: {self.current_process.pid})")

            try:
                # Send SIGTERM first
                self.current_process.terminate()

                # Wait up to 10 seconds for graceful shutdown
                try:
                    self.current_process.wait(timeout=10)
                    print(f"[Cleanup] ✓ Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    # Force kill if needed
                    print(f"[Cleanup] Process didn't terminate, forcing kill...")
                    self.current_process.kill()
                    self.current_process.wait()
                    print(f"[Cleanup] ✓ Process killed")

            except Exception as e:
                print(f"[Cleanup] Error stopping process: {e}")

            self.current_process = None

    def clean_qdrant(self):
        """Clean Qdrant collections."""
        print(f"\n[Cleanup] Cleaning Qdrant database...")

        try:
            client = QdrantClient(url=self.qdrant_url)

            # Get all collections with hephaestus prefix
            collections = client.get_collections()
            hephaestus_collections = [
                coll for coll in collections.collections
                if coll.name.startswith("hephaestus")
            ]

            if not hephaestus_collections:
                print(f"[Cleanup] No collections to clean")
                return

            print(f"[Cleanup] Found {len(hephaestus_collections)} collections")

            # Delete each collection
            for coll in hephaestus_collections:
                print(f"[Cleanup] Deleting {coll.name}...", end=" ")
                client.delete_collection(collection_name=coll.name)
                print("✓")

            print(f"[Cleanup] ✅ Qdrant cleaned successfully")

        except Exception as e:
            print(f"[Cleanup] ⚠️  Error cleaning Qdrant: {e}")
            print(f"[Cleanup] Continuing anyway...")

    def run_instance(self, instance_id: str) -> bool:
        """Run a single instance workflow.

        Returns:
            True if successful (validated result collected), False otherwise
        """
        start_time = time.time()

        # Create unique temporary workspace for this instance
        instance_workspace = Path(tempfile.mkdtemp(prefix=f"swebench_{instance_id}_"))
        print(f"\n[Setup] Created temp workspace: {instance_workspace}")

        try:
            # Start workflow
            process = self.start_workflow(instance_id, instance_workspace)

            # Wait 2 minutes before starting to poll (avoid picking up stale results)
            print(f"\n[Monitor] Waiting 2 minutes before polling (to avoid stale results)...")
            time.sleep(120)
            print(f"[Monitor] Starting to monitor for validated result...")
            print(f"[Monitor] Polling interval: {self.poll_interval}s")
            print(f"[Monitor] Timeout: {self.timeout}s")

            while True:
                # Check if process is still running
                if process.poll() is not None:
                    print(f"\n[Monitor] ⚠️  Workflow process exited with code {process.returncode}")

                    # Try one more time to get result
                    result = self.poll_for_result(instance_id, start_time)
                    if result:
                        end_time = time.time()
                        self.collect_results(instance_id, result, start_time, end_time)
                        return True
                    else:
                        print(f"[Monitor] ❌ No validated result found after process exit")
                        return False

                # Poll for result
                result = self.poll_for_result(instance_id, start_time)

                if result:
                    # Found validated result!
                    end_time = time.time()
                    self.collect_results(instance_id, result, start_time, end_time)
                    return True

                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > self.timeout:
                    print(f"[Monitor] ⏰ Timeout reached")
                    return False

                # Wait before next poll
                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            print(f"\n[Monitor] ⚠️  Interrupted by user")
            raise
        except Exception as e:
            print(f"\n[Monitor] ❌ Error running instance: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Always stop the workflow process
            self.stop_workflow()

            # Note: Workspace is kept at {instance_workspace} for inspection

    def run_batch(self):
        """Run all instances in batch."""
        print(f"\n{'='*70}")
        print(f"SWEBENCH BATCH RUNNER")
        print(f"{'='*70}\n")

        # Setup
        self.setup_directories()
        instances = self.load_instances()
        self.stats["total"] = len(instances)

        print(f"\n[Batch] Processing {len(instances)} instances")
        print(f"[Batch] Results will be saved to: {self.results_dir}")
        print(f"[Batch] Timeout per instance: {self.timeout}s ({self.timeout/3600:.1f}h)")

        # Process each instance
        for i, instance_id in enumerate(instances, 1):
            print(f"\n{'='*70}")
            print(f"INSTANCE {i}/{len(instances)}: {instance_id}")
            print(f"{'='*70}")

            try:
                # Run instance
                success = self.run_instance(instance_id)

                if success:
                    self.stats["completed"] += 1
                    print(f"\n[Batch] ✅ Instance {instance_id} completed successfully")
                else:
                    self.stats["failed"] += 1
                    print(f"\n[Batch] ❌ Instance {instance_id} failed or timed out")

            except KeyboardInterrupt:
                print(f"\n\n[Batch] ⚠️  Batch run interrupted by user")
                self.stop_workflow()
                break
            except Exception as e:
                print(f"\n[Batch] ❌ Unexpected error processing {instance_id}: {e}")
                self.stats["failed"] += 1

            finally:
                # Cleanup between instances (unless this is the last one)
                if i < len(instances):
                    print(f"\n[Batch] Cleaning up before next instance...")
                    self.clean_qdrant()
                    time.sleep(5)  # Brief pause before next instance

        # Print final statistics
        self.print_statistics()

    def print_statistics(self):
        """Print final batch statistics."""
        print(f"\n{'='*70}")
        print(f"BATCH RUN COMPLETE")
        print(f"{'='*70}\n")

        print(f"Total instances: {self.stats['total']}")
        print(f"Completed:       {self.stats['completed']} ({self.stats['completed']/self.stats['total']*100:.1f}%)")
        print(f"Failed:          {self.stats['failed']} ({self.stats['failed']/self.stats['total']*100:.1f}%)")

        print(f"\nResults saved to: {self.results_dir}")
        print(f"Each instance has:")
        print(f"  - solution.patch (the fix)")
        print(f"  - hephaestus.db (execution logs)")
        print(f"  - result_metadata.json (result details)")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run multiple SWEBench instances sequentially",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example instances.yaml format:

  instances:
    - astropy__astropy-14365
    - django__django-13590
    - sympy__sympy-18199

Or simply:

  - astropy__astropy-14365
  - django__django-13590
  - sympy__sympy-18199

Example usage:
  python run_swebench_batch.py --instances instances.yaml
  python run_swebench_batch.py --instances instances.yaml --timeout 3600
        """
    )

    parser.add_argument(
        "--instances",
        required=True,
        help="YAML file containing list of instance IDs"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=7200,
        help="Timeout per instance in seconds (default: 7200 = 2 hours)"
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Seconds between API polls (default: 60)"
    )

    parser.add_argument(
        "--api-url",
        default="http://localhost:4000/api/results",
        help="API URL for results (default: http://localhost:4000/api/results)"
    )

    parser.add_argument(
        "--qdrant-url",
        default="http://localhost:6333",
        help="Qdrant URL (default: http://localhost:6333)"
    )

    parser.add_argument(
        "--db-path",
        default="./hephaestus.db",
        help="Path to hephaestus.db (default: ./hephaestus.db)"
    )

    args = parser.parse_args()

    # Create and run batch runner
    runner = SWEBenchBatchRunner(
        instances_file=args.instances,
        api_url=args.api_url,
        qdrant_url=args.qdrant_url,
        db_path=args.db_path,
        poll_interval=args.poll_interval,
        timeout=args.timeout,
    )

    try:
        runner.run_batch()
    except KeyboardInterrupt:
        print("\n\n[Main] Batch run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[Main] Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
