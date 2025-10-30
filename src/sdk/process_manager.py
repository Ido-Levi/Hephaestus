"""Process lifecycle management for Hephaestus services."""

import os
import signal
import subprocess
import time
import threading
from typing import Optional, Callable, Dict
from pathlib import Path

from src.sdk.exceptions import ProcessSpawnError, RestartError
from src.sdk.config import HephaestusConfig


class ProcessInfo:
    """Information about a managed process."""

    def __init__(self, name: str, process: subprocess.Popen, log_file: Path):
        self.name = name
        self.process = process
        self.log_file = log_file
        self.restart_count = 0
        self.last_restart = None


class ProcessManager:
    """
    Manages the lifecycle of Hephaestus backend and monitoring processes.

    Responsibilities:
    - Spawning processes with log redirection
    - Health monitoring via watchdog thread
    - Graceful shutdown and restart
    - Auto-restart on failure
    """

    def __init__(self, config: HephaestusConfig, log_dir: Path):
        self.config = config
        self.log_dir = log_dir
        self.processes: Dict[str, ProcessInfo] = {}
        self.running = False
        self.watchdog_thread: Optional[threading.Thread] = None
        self.error_callback: Optional[Callable] = None

    def spawn_backend(self) -> None:
        """Spawn the FastAPI backend process with log redirection."""
        log_file = self.log_dir / "backend.log"

        # Get project root (assuming we're in src/sdk/)
        project_root = Path(__file__).parent.parent.parent

        # Build environment
        env = os.environ.copy()
        env.update(self.config.to_env_dict())

        # Command to run
        cmd = [
            "python",
            str(project_root / "run_server.py"),
        ]

        try:
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=str(project_root),
                )

            self.processes["backend"] = ProcessInfo("backend", process, log_file)

        except Exception as e:
            raise ProcessSpawnError(f"Failed to spawn backend process: {e}")

    def spawn_monitor(self) -> None:
        """Spawn the monitoring process with log redirection."""
        log_file = self.log_dir / "monitor.log"

        # Get project root
        project_root = Path(__file__).parent.parent.parent

        # Build environment
        env = os.environ.copy()
        env.update(self.config.to_env_dict())

        # Command to run
        cmd = [
            "python",
            str(project_root / "run_monitor.py"),
        ]

        try:
            with open(log_file, "w") as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=str(project_root),
                )

            self.processes["monitor"] = ProcessInfo("monitor", process, log_file)

        except Exception as e:
            raise ProcessSpawnError(f"Failed to spawn monitor process: {e}")

    def is_process_alive(self, name: str) -> bool:
        """Check if a process is still running."""
        if name not in self.processes:
            return False

        process_info = self.processes[name]
        return process_info.process.poll() is None

    def stop_process(
        self, name: str, graceful: bool = True, timeout: int = 10
    ) -> None:
        """Stop a specific process."""
        if name not in self.processes:
            return

        process_info = self.processes[name]
        process = process_info.process

        if process.poll() is not None:
            # Already stopped
            return

        if graceful:
            # Send SIGTERM and wait
            process.terminate()
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill
                process.kill()
                process.wait()
        else:
            # Force kill immediately
            process.kill()
            process.wait()

    def restart_process(self, name: str) -> None:
        """Restart a specific process."""
        if name not in self.processes:
            raise RestartError(f"Cannot restart unknown process: {name}")

        # Stop the process
        self.stop_process(name, graceful=True, timeout=5)

        # Remove from processes dict
        process_info = self.processes.pop(name)

        # Increment restart count
        restart_count = process_info.restart_count + 1

        # Respawn based on name
        if name == "backend":
            self.spawn_backend()
        elif name == "monitor":
            self.spawn_monitor()
        else:
            raise RestartError(f"Unknown process type: {name}")

        # Update restart info
        self.processes[name].restart_count = restart_count
        self.processes[name].last_restart = time.time()

    def start_watchdog(self) -> None:
        """Start the watchdog thread that monitors process health."""
        if self.watchdog_thread is not None:
            return

        self.running = True

        def watchdog_loop():
            max_restarts = 3
            restart_window = 300  # 5 minutes

            while self.running:
                time.sleep(10)  # Check every 10 seconds

                for name, process_info in list(self.processes.items()):
                    if not self.is_process_alive(name):
                        # Process died
                        print(
                            f"[Watchdog] Process {name} died unexpectedly (exit code: {process_info.process.returncode})"
                        )

                        # Check restart count
                        if process_info.restart_count >= max_restarts:
                            # Check if restarts were in a short window
                            if (
                                process_info.last_restart
                                and time.time() - process_info.last_restart
                                < restart_window
                            ):
                                print(
                                    f"[Watchdog] Process {name} exceeded max restarts ({max_restarts}), not restarting"
                                )
                                if self.error_callback:
                                    self.error_callback(
                                        f"Process {name} failed repeatedly"
                                    )
                                continue

                        # Attempt restart
                        try:
                            print(f"[Watchdog] Attempting to restart {name}...")
                            self.restart_process(name)
                            print(f"[Watchdog] Successfully restarted {name}")
                        except Exception as e:
                            print(f"[Watchdog] Failed to restart {name}: {e}")
                            if self.error_callback:
                                self.error_callback(f"Failed to restart {name}: {e}")

        self.watchdog_thread = threading.Thread(
            target=watchdog_loop, daemon=True, name="ProcessWatchdog"
        )
        self.watchdog_thread.start()

    def stop_watchdog(self) -> None:
        """Stop the watchdog thread."""
        self.running = False
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=5)
            self.watchdog_thread = None

    def shutdown_all(self, graceful: bool = True, timeout: int = 10) -> None:
        """Shutdown all managed processes."""
        self.stop_watchdog()

        for name in list(self.processes.keys()):
            self.stop_process(name, graceful=graceful, timeout=timeout)

        self.processes.clear()

    def get_log_path(self, name: str) -> Optional[Path]:
        """Get the log file path for a process."""
        if name in self.processes:
            return self.processes[name].log_file
        return None
