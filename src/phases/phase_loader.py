"""Phase loader for parsing and loading workflow phases from YAML files."""

import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import re

from src.phases.models import PhaseDefinition, WorkflowDefinition, PhasesConfig

logger = logging.getLogger(__name__)


class PhaseLoader:
    """Loads and parses workflow phases from YAML files."""

    @staticmethod
    def load_phases_from_folder(folder_path: str) -> WorkflowDefinition:
        """Load all phases from a folder containing YAML files.

        Args:
            folder_path: Path to folder containing phase YAML files

        Returns:
            WorkflowDefinition with loaded phases

        Raises:
            ValueError: If folder doesn't exist or contains invalid files
        """
        logger.info(f"PhaseLoader.load_phases_from_folder called with: '{folder_path}'")

        folder = Path(folder_path)
        logger.info(f"Resolved folder path: {folder}")
        logger.info(f"Folder absolute path: {folder.absolute()}")

        if not folder.exists():
            logger.error(f"Folder does not exist: {folder_path}")
            raise ValueError(f"Phases folder not found: {folder_path}")

        if not folder.is_dir():
            logger.error(f"Path is not a directory: {folder_path}")
            raise ValueError(f"Path is not a directory: {folder_path}")

        # Find all YAML files matching the pattern
        all_yaml_files = list(folder.glob("*.yaml"))
        logger.info(f"All YAML files in folder: {[f.name for f in all_yaml_files]}")

        pattern = r'^\d{2}_[\w_]+\.yaml$'
        logger.info(f"Looking for files matching pattern: {pattern}")

        yaml_files = sorted([
            f for f in folder.glob("*.yaml")
            if re.match(pattern, f.name)
        ])

        logger.info(f"Files matching pattern: {[f.name for f in yaml_files]}")

        if not yaml_files:
            logger.error(f"No files matched the required pattern: {pattern}")
            raise ValueError(
                f"No valid phase YAML files found in {folder_path}. "
                "Files must follow pattern: XX_phase_name.yaml"
            )

        phases = []
        for yaml_file in yaml_files:
            try:
                phase = PhaseLoader._load_single_phase(yaml_file)
                phases.append(phase)
                logger.info(f"Loaded phase: {phase.name} (order: {phase.order})")
            except Exception as e:
                logger.error(f"Failed to load phase from {yaml_file}: {e}")
                raise ValueError(f"Failed to load phase from {yaml_file.name}: {e}")

        # Verify phase order continuity (optional, can have gaps)
        PhaseLoader._validate_phase_order(phases)

        # Extract workflow name from folder
        workflow_name = folder.name.replace('_', ' ').title()

        return WorkflowDefinition(
            name=workflow_name,
            phases_folder=folder_path,
            phases=phases
        )

    @staticmethod
    def _load_single_phase(file_path: Path) -> PhaseDefinition:
        """Load a single phase from a YAML file.

        Args:
            file_path: Path to YAML file

        Returns:
            PhaseDefinition instance
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            if not content:
                raise ValueError("Empty YAML file")

            # Create phase definition from YAML content
            phase = PhaseDefinition.from_yaml_content(
                filename=file_path.name,
                content=content
            )

            return phase

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing phase file: {e}")

    @staticmethod
    def _validate_phase_order(phases: List[PhaseDefinition]) -> None:
        """Validate that phase orders are unique and properly ordered.

        Args:
            phases: List of phase definitions

        Raises:
            ValueError: If phase orders are invalid
        """
        orders = [p.order for p in phases]

        # Check for duplicates
        if len(orders) != len(set(orders)):
            duplicate_orders = [o for o in orders if orders.count(o) > 1]
            raise ValueError(f"Duplicate phase orders found: {duplicate_orders}")

        # Phases should be in ascending order (but gaps are allowed)
        sorted_orders = sorted(orders)
        if orders != sorted_orders:
            raise ValueError(
                f"Phases are not in order. Expected: {sorted_orders}, Got: {orders}"
            )

    @staticmethod
    def validate_yaml_structure(content: Dict[str, Any]) -> List[str]:
        """Validate that YAML content has required fields.

        Args:
            content: Parsed YAML content

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check for required fields (case-insensitive)
        has_description = any(
            k.lower() == 'description' for k in content.keys()
        )
        has_done = any(
            k.lower() in ['done_definitions', 'done_definition']
            for k in content.keys()
        )

        if not has_description:
            errors.append("Missing required field: description")

        if not has_done:
            errors.append("Missing required field: done_definitions or Done_Definitions")

        return errors

    @staticmethod
    def create_example_phase(
        order: int,
        name: str,
        description: str,
        done_definitions: List[str],
        additional_notes: Optional[str] = None,
        outputs: Optional[str] = None,
        next_steps: Optional[str] = None,
        working_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an example phase dictionary for saving to YAML.

        Args:
            order: Phase order number (e.g., 1, 2, 3)
            name: Phase name (will be converted to snake_case for filename)
            description: Phase description
            done_definitions: List of completion criteria
            additional_notes: Optional additional notes
            outputs: Optional expected outputs
            next_steps: Optional next steps
            working_directory: Optional default working directory for agents

        Returns:
            Dictionary ready to be saved as YAML
        """
        phase_dict = {
            'description': description,
            'Done_Definitions': done_definitions,
        }

        if working_directory:
            phase_dict['working_directory'] = working_directory

        if additional_notes:
            phase_dict['Additional_Notes'] = additional_notes

        if outputs:
            phase_dict['Outputs'] = outputs

        if next_steps:
            phase_dict['Next_Steps'] = next_steps

        return phase_dict

    @staticmethod
    def save_phase_to_yaml(
        phase_dict: Dict[str, Any],
        order: int,
        name: str,
        folder_path: str
    ) -> str:
        """Save a phase dictionary to a YAML file.

        Args:
            phase_dict: Phase data dictionary
            order: Phase order number
            name: Phase name
            folder_path: Folder to save the YAML file

        Returns:
            Path to created YAML file
        """
        # Convert name to snake_case for filename
        filename_name = re.sub(r'[^\w\s]', '', name.lower())
        filename_name = re.sub(r'\s+', '_', filename_name)

        # Create filename with order prefix
        filename = f"{order:02d}_{filename_name}.yaml"
        file_path = os.path.join(folder_path, filename)

        # Ensure folder exists
        os.makedirs(folder_path, exist_ok=True)

        # Save to YAML
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(
                phase_dict,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )

        logger.info(f"Created phase file: {file_path}")
        return file_path

    @staticmethod
    def load_phases_config(folder_path: str) -> PhasesConfig:
        """Load phases configuration from phases_config.yaml.

        Args:
            folder_path: Path to folder containing phases_config.yaml

        Returns:
            PhasesConfig with loaded configuration or defaults if file missing

        Raises:
            ValueError: If configuration file is invalid
        """
        logger.info(f"PhaseLoader.load_phases_config called with: '{folder_path}'")

        folder = Path(folder_path)
        config_file = folder / "phases_config.yaml"

        if not config_file.exists():
            logger.info(f"No phases_config.yaml found in {folder_path}, using defaults")
            return PhasesConfig()

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = yaml.safe_load(f)

            if content is None:
                logger.warning(f"Empty phases_config.yaml in {folder_path}, using defaults")
                return PhasesConfig()

            logger.info(f"Loaded phases config from {config_file}")
            return PhasesConfig.from_yaml_content(content)

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse phases_config.yaml: {e}")
            raise ValueError(f"Invalid YAML in phases_config.yaml: {e}")
        except Exception as e:
            logger.error(f"Failed to load phases config: {e}")
            raise ValueError(f"Failed to load phases configuration: {e}")