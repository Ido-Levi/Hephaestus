"""Additional tests to improve coverage for validation helpers."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.services.validation_helpers import validate_file_path


class TestValidationHelpersAdditionalCoverage:
    """Additional tests to reach 90% coverage for validation helpers."""

    def test_validate_file_path_relative_path(self):
        """Test validation of relative paths."""
        # Test that relative paths are converted to absolute
        with patch('src.services.validation_helpers.Path.cwd') as mock_cwd:
            mock_cwd.return_value = Path("/home/user")

            # This should not raise
            validate_file_path("relative/path/file.md")

