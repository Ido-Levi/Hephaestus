#!/usr/bin/env python3
"""
Hephaestus Setup Validation Script for macOS
Checks all prerequisites and configuration requirements
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import yaml

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class SetupChecker:
    def __init__(self):
        self.results = {
            'cli_tools': {},
            'api_keys': {},
            'mcp_servers': {},
            'configuration': {},
            'working_directory': {},
            'services': {},
            'dependencies': {}
        }
        self.project_root = Path(__file__).parent

    def check_command(self, command: str, name: str = None) -> bool:
        """Check if a command exists in PATH"""
        if name is None:
            name = command
        exists = shutil.which(command) is not None
        self.results['cli_tools'][name] = exists
        return exists

    def check_python_version(self) -> Tuple[bool, str]:
        """Check Python version is 3.10+"""
        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        is_valid = version.major == 3 and version.minor >= 10
        self.results['cli_tools']['Python 3.10+'] = is_valid
        return is_valid, version_str

    def check_docker_running(self) -> bool:
        """Check if Docker daemon is running"""
        try:
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                timeout=5
            )
            is_running = result.returncode == 0
            self.results['services']['Docker daemon'] = is_running
            return is_running
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results['services']['Docker daemon'] = False
            return False

    def check_qdrant_running(self) -> bool:
        """Check if Qdrant is accessible"""
        try:
            result = subprocess.run(
                ['curl', '-s', 'http://localhost:6333/'],
                capture_output=True,
                timeout=5
            )
            is_running = result.returncode == 0 and b'qdrant' in result.stdout.lower()
            self.results['services']['Qdrant (port 6333)'] = is_running
            return is_running
        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results['services']['Qdrant (port 6333)'] = False
            return False

    def check_env_file(self) -> Dict[str, bool]:
        """Check .env file and required API keys"""
        env_path = self.project_root / '.env'

        if not env_path.exists():
            self.results['api_keys']['.env file exists'] = False
            return {}

        self.results['api_keys']['.env file exists'] = True

        # Read .env file
        env_vars = {}
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

        # Check required keys
        required_keys = ['OPENAI_API_KEY']
        optional_keys = ['OPENROUTER_API_KEY', 'ANTHROPIC_API_KEY']

        for key in required_keys:
            has_key = key in env_vars and env_vars[key] and env_vars[key] != ''
            self.results['api_keys'][key] = has_key

        for key in optional_keys:
            has_key = key in env_vars and env_vars[key] and env_vars[key] != ''
            self.results['api_keys'][f'{key} (optional)'] = has_key

        return env_vars

    def check_mcp_servers(self) -> bool:
        """Check if MCP servers are configured in Claude Code"""
        try:
            result = subprocess.run(
                ['claude', 'mcp', 'list'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                self.results['mcp_servers']['Claude MCP accessible'] = False
                return False

            self.results['mcp_servers']['Claude MCP accessible'] = True
            output = result.stdout.lower()

            # Check for Hephaestus and Qdrant servers
            has_hephaestus = 'hephaestus' in output
            has_qdrant = 'qdrant' in output

            self.results['mcp_servers']['Hephaestus MCP server'] = has_hephaestus
            self.results['mcp_servers']['Qdrant MCP server'] = has_qdrant

            return has_hephaestus and has_qdrant

        except (subprocess.TimeoutExpired, FileNotFoundError):
            self.results['mcp_servers']['Claude MCP accessible'] = False
            return False

    def check_config_file(self) -> Dict:
        """Check hephaestus_config.yaml"""
        config_path = self.project_root / 'hephaestus_config.yaml'

        if not config_path.exists():
            self.results['configuration']['hephaestus_config.yaml exists'] = False
            return {}

        self.results['configuration']['hephaestus_config.yaml exists'] = True

        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)

            # Check for required paths
            has_project_root = 'paths' in config and 'project_root' in config['paths']
            has_main_repo = 'git' in config and 'main_repo_path' in config['git']

            self.results['configuration']['project_root configured'] = has_project_root
            self.results['configuration']['main_repo_path configured'] = has_main_repo

            return config

        except Exception as e:
            self.results['configuration']['Config file is valid YAML'] = False
            return {}

    def check_working_directory(self, config: Dict) -> bool:
        """Check working directory setup"""
        if 'paths' not in config or 'project_root' not in config['paths']:
            self.results['working_directory']['Project root path exists'] = False
            return False

        project_path = Path(config['paths']['project_root']).expanduser()

        # Check if directory exists
        exists = project_path.exists()
        self.results['working_directory']['Project directory exists'] = exists

        if not exists:
            return False

        # Check if it's a git repository
        is_git = (project_path / '.git').exists()
        self.results['working_directory']['Is git repository'] = is_git

        if is_git:
            # Check if it has commits
            try:
                result = subprocess.run(
                    ['git', '-C', str(project_path), 'rev-parse', 'HEAD'],
                    capture_output=True,
                    timeout=5
                )
                has_commits = result.returncode == 0
                self.results['working_directory']['Has at least one commit'] = has_commits
            except:
                self.results['working_directory']['Has at least one commit'] = False

        # Check for PRD.md (optional)
        has_prd = (project_path / 'PRD.md').exists()
        self.results['working_directory']['PRD.md exists (optional)'] = has_prd

        return exists and is_git

    def check_python_dependencies(self) -> bool:
        """Check if Python dependencies are installed"""
        try:
            # Try importing key modules
            import fastapi
            self.results['dependencies']['fastapi installed'] = True
        except ImportError:
            self.results['dependencies']['fastapi installed'] = False

        try:
            import qdrant_client
            self.results['dependencies']['qdrant-client installed'] = True
        except ImportError:
            self.results['dependencies']['qdrant-client installed'] = False

        try:
            import sqlalchemy
            self.results['dependencies']['sqlalchemy installed'] = True
        except ImportError:
            self.results['dependencies']['sqlalchemy installed'] = False

        # Check if requirements.txt exists
        req_exists = (self.project_root / 'requirements.txt').exists()
        self.results['dependencies']['requirements.txt exists'] = req_exists

        return all([
            self.results['dependencies'].get('fastapi installed', False),
            self.results['dependencies'].get('qdrant-client installed', False),
            self.results['dependencies'].get('sqlalchemy installed', False)
        ])

    def check_frontend_dependencies(self) -> bool:
        """Check if frontend dependencies are installed"""
        frontend_path = self.project_root / 'frontend'

        if not frontend_path.exists():
            self.results['dependencies']['frontend/ directory exists'] = False
            return False

        self.results['dependencies']['frontend/ directory exists'] = True

        node_modules = frontend_path / 'node_modules'
        has_modules = node_modules.exists()
        self.results['dependencies']['frontend/node_modules exists'] = has_modules

        package_json = frontend_path / 'package.json'
        has_package = package_json.exists()
        self.results['dependencies']['frontend/package.json exists'] = has_package

        return has_modules

    def run_all_checks(self):
        """Run all validation checks"""
        print(f"{Colors.BOLD}{Colors.BLUE}🔍 Hephaestus Setup Validation{Colors.END}\n")

        # CLI Tools
        print(f"{Colors.BOLD}Checking CLI Tools...{Colors.END}")
        self.check_command('tmux')
        self.check_command('git')
        self.check_command('docker')
        self.check_command('node')
        self.check_command('npm')
        self.check_command('claude', 'Claude Code')
        self.check_command('opencode', 'OpenCode (optional)')
        python_ok, python_version = self.check_python_version()

        # API Keys
        print(f"{Colors.BOLD}Checking API Keys...{Colors.END}")
        self.check_env_file()

        # MCP Servers
        print(f"{Colors.BOLD}Checking MCP Servers...{Colors.END}")
        self.check_mcp_servers()

        # Configuration
        print(f"{Colors.BOLD}Checking Configuration...{Colors.END}")
        config = self.check_config_file()

        # Working Directory
        print(f"{Colors.BOLD}Checking Working Directory...{Colors.END}")
        self.check_working_directory(config)

        # Services
        print(f"{Colors.BOLD}Checking Services...{Colors.END}")
        self.check_docker_running()
        self.check_qdrant_running()

        # Dependencies
        print(f"{Colors.BOLD}Checking Dependencies...{Colors.END}")
        self.check_python_dependencies()
        self.check_frontend_dependencies()

    def print_summary(self):
        """Print a summary of all checks"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}SETUP VALIDATION SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

        total_checks = 0
        passed_checks = 0

        for category, checks in self.results.items():
            if not checks:
                continue

            # Print category header
            category_name = category.replace('_', ' ').title()
            print(f"{Colors.BOLD}{category_name}:{Colors.END}")

            for item, status in checks.items():
                total_checks += 1
                if status:
                    passed_checks += 1
                    print(f"  {Colors.GREEN}✓{Colors.END} {item}")
                else:
                    print(f"  {Colors.RED}✗{Colors.END} {item}")

            print()

        # Overall status
        print(f"{Colors.BOLD}{'='*60}{Colors.END}")
        percentage = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        if percentage == 100:
            color = Colors.GREEN
            status = "✓ ALL CHECKS PASSED"
        elif percentage >= 80:
            color = Colors.YELLOW
            status = "⚠ MOSTLY READY (some optional items missing)"
        else:
            color = Colors.RED
            status = "✗ SETUP INCOMPLETE"

        print(f"{color}{Colors.BOLD}{status}{Colors.END}")
        print(f"{Colors.BOLD}Passed: {passed_checks}/{total_checks} ({percentage:.1f}%){Colors.END}")
        print(f"{Colors.BOLD}{'='*60}{Colors.END}\n")

def main():
    checker = SetupChecker()
    checker.run_all_checks()
    checker.print_summary()

if __name__ == '__main__':
    main()
