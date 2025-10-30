"""Tests for phase loading functionality."""

import pytest
import tempfile
import yaml
from pathlib import Path

from src.sdk.models import Phase
from src.sdk.client import HephaestusSDK


def create_test_phase_yaml(path: Path, phase_id: int, name: str):
    """Helper to create a test phase YAML file."""
    data = {
        "description": f"Phase {phase_id} description",
        "Done_Definitions": [
            f"Task {phase_id} completed",
            "All tests pass",
        ],
        "working_directory": "/test/path",
        "Additional_Notes": f"Notes for phase {phase_id}",
        "Outputs": [f"output{phase_id}.md"],
        "Next_Steps": [f"Phase {phase_id + 1}: Next phase"],
    }

    filename = f"{phase_id:02d}_{name}.yaml"
    filepath = path / filename

    with open(filepath, "w") as f:
        yaml.dump(data, f)


def test_load_phases_from_yaml():
    """Test loading phases from YAML directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test phase files
        create_test_phase_yaml(tmppath, 1, "planning")
        create_test_phase_yaml(tmppath, 2, "implementation")
        create_test_phase_yaml(tmppath, 3, "validation")

        # Set API key for config validation
        import os

        os.environ["ANTHROPIC_API_KEY"] = "test-key"

        try:
            # Load SDK with phases directory
            sdk = HephaestusSDK(phases_dir=str(tmppath))

            # Check phases loaded correctly
            assert len(sdk.phases_map) == 3
            assert 1 in sdk.phases_map
            assert 2 in sdk.phases_map
            assert 3 in sdk.phases_map

            # Check phase 1
            phase1 = sdk.phases_map[1]
            assert phase1.name == "planning"
            assert phase1.description == "Phase 1 description"
            assert len(phase1.done_definitions) == 2

        finally:
            del os.environ["ANTHROPIC_API_KEY"]


def test_load_phases_from_python_objects():
    """Test loading phases from Python objects."""
    import os

    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    try:
        phases = [
            Phase(
                id=1,
                name="planning",
                description="Plan the work",
                done_definitions=["Plan created"],
                working_directory="/test",
            ),
            Phase(
                id=2,
                name="implementation",
                description="Implement the work",
                done_definitions=["Code written"],
                working_directory="/test",
            ),
        ]

        sdk = HephaestusSDK(phases=phases)

        assert len(sdk.phases_map) == 2
        assert sdk.phases_map[1].name == "planning"
        assert sdk.phases_map[2].name == "implementation"

    finally:
        del os.environ["ANTHROPIC_API_KEY"]


def test_cannot_provide_both_phases_dir_and_phases():
    """Test that providing both phases_dir and phases raises error."""
    import os

    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    try:
        phases = [
            Phase(
                id=1,
                name="test",
                description="Test",
                done_definitions=["Done"],
                working_directory=".",
            )
        ]

        with pytest.raises(ValueError, match="Cannot provide both"):
            HephaestusSDK(phases_dir="/some/path", phases=phases)

    finally:
        del os.environ["ANTHROPIC_API_KEY"]


def test_must_provide_either_phases_dir_or_phases():
    """Test that at least one of phases_dir or phases must be provided."""
    import os

    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    try:
        with pytest.raises(ValueError, match="Either phases_dir or phases must be provided"):
            HephaestusSDK()

    finally:
        del os.environ["ANTHROPIC_API_KEY"]


def test_duplicate_phase_ids_rejected():
    """Test that duplicate phase IDs are rejected."""
    import os

    os.environ["ANTHROPIC_API_KEY"] = "test-key"

    try:
        phases = [
            Phase(
                id=1,
                name="first",
                description="First",
                done_definitions=["Done"],
                working_directory=".",
            ),
            Phase(
                id=1,  # Duplicate ID
                name="second",
                description="Second",
                done_definitions=["Done"],
                working_directory=".",
            ),
        ]

        with pytest.raises(ValueError, match="Duplicate phase ID"):
            HephaestusSDK(phases=phases)

    finally:
        del os.environ["ANTHROPIC_API_KEY"]
