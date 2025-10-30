"""Tests for phases configuration loading."""

import os
import tempfile
import yaml
import pytest
from pathlib import Path

from src.phases.models import PhasesConfig
from src.phases.phase_loader import PhaseLoader


class TestPhasesConfig:
    """Test cases for phases configuration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_config_file(self, config_data):
        """Helper to create a phases_config.yaml file."""
        config_path = Path(self.temp_dir) / "phases_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        return str(config_path)

    def test_phases_config_validation_valid(self):
        """Test valid phases configuration."""
        config = PhasesConfig(
            has_result=True,
            result_criteria="Must provide correct password with execution proof",
            on_result_found="stop_all"
        )

        assert config.has_result == True
        assert "password" in config.result_criteria
        assert config.on_result_found == "stop_all"

    def test_phases_config_validation_missing_criteria(self):
        """Test validation error when has_result=True but no criteria."""
        with pytest.raises(ValueError, match="result_criteria must be provided"):
            PhasesConfig(
                has_result=True,
                result_criteria=None,
                on_result_found="stop_all"
            )

    def test_phases_config_defaults(self):
        """Test default values for phases configuration."""
        config = PhasesConfig()

        assert config.has_result == False
        assert config.result_criteria is None
        assert config.on_result_found == "do_nothing"

    def test_phases_config_from_yaml_content(self):
        """Test creating config from YAML content."""
        yaml_content = {
            "has_result": True,
            "result_criteria": "Must solve the challenge and provide proof",
            "on_result_found": "stop_all"
        }

        config = PhasesConfig.from_yaml_content(yaml_content)

        assert config.has_result == True
        assert config.result_criteria == "Must solve the challenge and provide proof"
        assert config.on_result_found == "stop_all"

    def test_phases_config_from_yaml_content_partial(self):
        """Test creating config from partial YAML content."""
        yaml_content = {
            "has_result": True,
            "result_criteria": "Some criteria"
        }
        # on_result_found missing, should default

        config = PhasesConfig.from_yaml_content(yaml_content)

        assert config.has_result == True
        assert config.result_criteria == "Some criteria"
        assert config.on_result_found == "do_nothing"  # default

    def test_load_phases_config_file_exists(self):
        """Test loading configuration from existing file."""
        config_data = {
            "has_result": True,
            "result_criteria": "Find the flag and prove it works",
            "on_result_found": "stop_all"
        }
        self.create_config_file(config_data)

        config = PhaseLoader.load_phases_config(self.temp_dir)

        assert config.has_result == True
        assert config.result_criteria == "Find the flag and prove it works"
        assert config.on_result_found == "stop_all"

    def test_load_phases_config_file_missing(self):
        """Test loading configuration when file doesn't exist."""
        # No config file created
        config = PhaseLoader.load_phases_config(self.temp_dir)

        # Should return defaults
        assert config.has_result == False
        assert config.result_criteria is None
        assert config.on_result_found == "do_nothing"

    def test_load_phases_config_empty_file(self):
        """Test loading configuration from empty file."""
        config_path = Path(self.temp_dir) / "phases_config.yaml"
        with open(config_path, 'w') as f:
            f.write("")  # Empty file

        config = PhaseLoader.load_phases_config(self.temp_dir)

        # Should return defaults
        assert config.has_result == False
        assert config.result_criteria is None
        assert config.on_result_found == "do_nothing"

    def test_load_phases_config_invalid_yaml(self):
        """Test loading configuration from invalid YAML file."""
        config_path = Path(self.temp_dir) / "phases_config.yaml"
        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML

        with pytest.raises(ValueError, match="Invalid YAML"):
            PhaseLoader.load_phases_config(self.temp_dir)

    def test_crackme_challenge_config(self):
        """Test configuration for a crackme challenge."""
        config_data = {
            "has_result": True,
            "result_criteria": """Must provide:
1. The correct password or flag
2. Execution proof showing successful unlock
3. Method used to find the solution""",
            "on_result_found": "stop_all"
        }
        self.create_config_file(config_data)

        config = PhaseLoader.load_phases_config(self.temp_dir)

        assert config.has_result == True
        assert "password or flag" in config.result_criteria
        assert "execution proof" in config.result_criteria
        assert config.on_result_found == "stop_all"

    def test_research_task_config(self):
        """Test configuration for a research task."""
        config_data = {
            "has_result": True,
            "result_criteria": """Must include:
1. Comprehensive analysis with 5+ sources
2. Actionable recommendations
3. Evidence-based conclusions""",
            "on_result_found": "do_nothing"
        }
        self.create_config_file(config_data)

        config = PhaseLoader.load_phases_config(self.temp_dir)

        assert config.has_result == True
        assert "5+ sources" in config.result_criteria
        assert "recommendations" in config.result_criteria
        assert config.on_result_found == "do_nothing"

    def test_bug_hunt_config(self):
        """Test configuration for a bug hunt task."""
        config_data = {
            "has_result": True,
            "result_criteria": """Must demonstrate:
1. Root cause identified
2. Fix implemented and tested
3. All tests passing""",
            "on_result_found": "stop_all"
        }
        self.create_config_file(config_data)

        config = PhaseLoader.load_phases_config(self.temp_dir)

        assert config.has_result == True
        assert "root cause" in config.result_criteria.lower()
        assert "fix implemented" in config.result_criteria.lower()
        assert "tests passing" in config.result_criteria.lower()
        assert config.on_result_found == "stop_all"

    def test_invalid_on_result_found_value(self):
        """Test validation of on_result_found values."""
        with pytest.raises(ValueError):
            PhasesConfig(
                has_result=True,
                result_criteria="Some criteria",
                on_result_found="invalid_action"  # Not allowed
            )