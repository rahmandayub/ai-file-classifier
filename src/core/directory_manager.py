"""Directory creation and management module."""

import re
from pathlib import Path
from typing import Dict, List, Optional

from ..models.classification import Classification
from ..models.file_info import FileInfo
from ..utils.logger import get_logger
from ..utils.validators import FilenameValidator

logger = get_logger()


class NamingConvention:
    """Handles different naming conventions for directories."""

    @staticmethod
    def to_snake_case(text: str) -> str:
        """
        Convert text to snake_case.

        Args:
            text: Input text

        Returns:
            snake_case formatted text
        """
        # Replace spaces and hyphens with underscores
        text = re.sub(r'[\s\-]+', '_', text)
        # Insert underscore before capital letters
        text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        # Convert to lowercase
        text = text.lower()
        # Remove consecutive underscores
        text = re.sub(r'_+', '_', text)
        # Remove leading/trailing underscores
        text = text.strip('_')
        return text

    @staticmethod
    def to_kebab_case(text: str) -> str:
        """
        Convert text to kebab-case.

        Args:
            text: Input text

        Returns:
            kebab-case formatted text
        """
        # Similar to snake_case but use hyphens
        text = re.sub(r'[\s_]+', '-', text)
        text = re.sub(r'([a-z])([A-Z])', r'\1-\2', text)
        text = text.lower()
        text = re.sub(r'-+', '-', text)
        text = text.strip('-')
        return text

    @staticmethod
    def to_pascal_case(text: str) -> str:
        """
        Convert text to PascalCase.

        Args:
            text: Input text

        Returns:
            PascalCase formatted text
        """
        # Split on spaces, hyphens, underscores
        words = re.split(r'[\s\-_]+', text)
        # Capitalize first letter of each word
        words = [word.capitalize() for word in words if word]
        return ''.join(words)

    @staticmethod
    def to_camel_case(text: str) -> str:
        """
        Convert text to camelCase.

        Args:
            text: Input text

        Returns:
            camelCase formatted text
        """
        pascal = NamingConvention.to_pascal_case(text)
        if pascal:
            # Make first letter lowercase
            return pascal[0].lower() + pascal[1:]
        return pascal

    @staticmethod
    def apply_convention(text: str, convention: str) -> str:
        """
        Apply specified naming convention.

        Args:
            text: Input text
            convention: Convention name (snake_case, kebab-case, PascalCase, camelCase)

        Returns:
            Formatted text
        """
        convention = convention.lower().replace('-', '_')

        if convention == 'snake_case':
            return NamingConvention.to_snake_case(text)
        elif convention in ('kebab_case', 'kebab'):
            return NamingConvention.to_kebab_case(text)
        elif convention in ('pascalcase', 'pascal'):
            return NamingConvention.to_pascal_case(text)
        elif convention in ('camelcase', 'camel'):
            return NamingConvention.to_camel_case(text)
        else:
            logger.warning(f"Unknown naming convention: {convention}, using snake_case")
            return NamingConvention.to_snake_case(text)


class DirectoryManager:
    """Manages directory creation and naming."""

    def __init__(
        self,
        base_path: Path,
        naming_convention: str = "snake_case",
        sanitize_names: bool = True,
        max_name_length: int = 100,
        conflict_resolution: str = "append_counter"
    ):
        """
        Initialize the directory manager.

        Args:
            base_path: Base directory path for organization
            naming_convention: Naming convention to use
            sanitize_names: Whether to sanitize directory names
            max_name_length: Maximum directory name length
            conflict_resolution: How to resolve name conflicts
        """
        self.base_path = base_path
        self.naming_convention = naming_convention
        self.sanitize_names = sanitize_names
        self.max_name_length = max_name_length
        self.conflict_resolution = conflict_resolution
        self.created_directories: set = set()

    def create_structure(
        self,
        classification_map: Dict[FileInfo, Classification],
        dry_run: bool = False
    ) -> Dict[str, Path]:
        """
        Create directory structure from classification map.

        Args:
            classification_map: Mapping of files to classifications
            dry_run: If True, don't actually create directories

        Returns:
            Dictionary mapping classification paths to actual paths
        """
        directory_paths = {}

        # Collect unique directory paths
        unique_paths = set()
        for classification in classification_map.values():
            if classification:
                unique_paths.add(classification.directory_path)

        # Create directories
        for dir_path in sorted(unique_paths):
            actual_path = self.generate_path(dir_path)
            directory_paths[dir_path] = actual_path

            if not dry_run:
                self._create_directory(actual_path)

        logger.info(f"{'Would create' if dry_run else 'Created'} {len(directory_paths)} directories")
        return directory_paths

    def generate_path(self, classification_path: str) -> Path:
        """
        Generate actual file system path from classification path.

        Args:
            classification_path: Classification path (e.g., "documents/reports")

        Returns:
            Actual Path object
        """
        # Split into components
        components = classification_path.split('/')

        # Process each component
        processed = []
        for component in components:
            # Sanitize if enabled
            if self.sanitize_names:
                component = self.sanitize_name(component)

            # Apply naming convention
            component = NamingConvention.apply_convention(
                component,
                self.naming_convention
            )

            # Ensure it's a valid directory name
            if not component or component in ('.', '..'):
                component = 'unnamed'

            processed.append(component)

        # Build full path
        full_path = self.base_path
        for component in processed:
            full_path = full_path / component

        return full_path

    def sanitize_name(self, name: str) -> str:
        """
        Sanitize directory name.

        Args:
            name: Directory name

        Returns:
            Sanitized name
        """
        # Use filename validator
        sanitized = FilenameValidator.sanitize_filename(name)

        # Limit length
        if len(sanitized) > self.max_name_length:
            sanitized = sanitized[:self.max_name_length]

        # Remove trailing dots/spaces
        sanitized = sanitized.rstrip('. ')

        return sanitized or 'unnamed'

    def resolve_conflict(self, path: Path) -> Path:
        """
        Resolve directory name conflict.

        Args:
            path: Original path

        Returns:
            Resolved path
        """
        if not path.exists():
            return path

        if self.conflict_resolution == 'skip':
            return path

        parent = path.parent
        name = path.name

        if self.conflict_resolution == 'append_counter':
            counter = 2
            while True:
                new_name = f"{name}_{counter}"
                new_path = parent / new_name
                if not new_path.exists():
                    logger.debug(f"Resolved conflict: {name} -> {new_name}")
                    return new_path
                counter += 1

        elif self.conflict_resolution == 'append_timestamp':
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            new_name = f"{name}_{timestamp}"
            new_path = parent / new_name
            logger.debug(f"Resolved conflict: {name} -> {new_name}")
            return new_path

        elif self.conflict_resolution == 'append_hash':
            import hashlib
            hash_val = hashlib.sha256(str(path).encode()).hexdigest()[:6]
            new_name = f"{name}_{hash_val}"
            new_path = parent / new_name
            logger.debug(f"Resolved conflict: {name} -> {new_name}")
            return new_path

        else:
            # Default to counter
            return self.resolve_conflict(path)

    def _create_directory(self, path: Path) -> None:
        """
        Create directory and any necessary parent directories.

        Args:
            path: Directory path to create
        """
        try:
            if path not in self.created_directories:
                path.mkdir(parents=True, exist_ok=True)
                self.created_directories.add(path)
                logger.debug(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Failed to create directory {path}: {e}")
            raise

    def get_destination_path(
        self,
        file_info: FileInfo,
        classification: Classification
    ) -> Path:
        """
        Get the full destination path for a file.

        Args:
            file_info: File information
            classification: Classification result

        Returns:
            Full destination path including filename
        """
        dir_path = self.generate_path(classification.directory_path)
        return dir_path / file_info.name


def create_directory_manager_from_config(
    base_path: Path,
    config: dict
) -> DirectoryManager:
    """
    Create DirectoryManager from configuration.

    Args:
        base_path: Base directory path
        config: Directory configuration

    Returns:
        DirectoryManager instance
    """
    return DirectoryManager(
        base_path=base_path,
        naming_convention=config.get('naming_convention', 'snake_case'),
        sanitize_names=config.get('sanitize_names', True),
        max_name_length=config.get('max_name_length', 100),
        conflict_resolution=config.get('conflict_resolution', 'append_counter')
    )
