"""Input validation utilities for the AI File Classifier."""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from .exceptions import ValidationError


class PathValidator:
    """Validates file system paths."""

    @staticmethod
    def validate_path(path: str, must_exist: bool = True) -> Path:
        """
        Validate a file system path.

        Args:
            path: Path to validate
            must_exist: Whether path must exist

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is invalid
        """
        if not path:
            raise ValidationError("Path cannot be empty")

        try:
            path_obj = Path(path).resolve()
        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid path: {e}")

        if must_exist and not path_obj.exists():
            raise ValidationError(f"Path does not exist: {path}")

        # Prevent directory traversal
        try:
            path_obj.resolve().relative_to(Path.cwd().resolve())
        except ValueError:
            # Path is outside current directory - still valid
            pass

        return path_obj

    @staticmethod
    def validate_directory(path: str, must_exist: bool = True) -> Path:
        """
        Validate a directory path.

        Args:
            path: Directory path to validate
            must_exist: Whether directory must exist

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is not a directory
        """
        path_obj = PathValidator.validate_path(path, must_exist)

        if must_exist and not path_obj.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")

        return path_obj

    @staticmethod
    def validate_file(path: str, must_exist: bool = True) -> Path:
        """
        Validate a file path.

        Args:
            path: File path to validate
            must_exist: Whether file must exist

        Returns:
            Validated Path object

        Raises:
            ValidationError: If path is not a file
        """
        path_obj = PathValidator.validate_path(path, must_exist)

        if must_exist and not path_obj.is_file():
            raise ValidationError(f"Path is not a file: {path}")

        return path_obj


class FilenameValidator:
    """Validates and sanitizes filenames."""

    # Characters not allowed in filenames on most systems
    INVALID_CHARS = r'[<>:"/\\|?*\x00-\x1f]'

    # Maximum filename length (conservative for cross-platform)
    MAX_LENGTH = 255

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize a filename by removing invalid characters.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        sanitized = re.sub(FilenameValidator.INVALID_CHARS, '_', filename)

        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip('. ')

        # Limit length
        if len(sanitized) > FilenameValidator.MAX_LENGTH:
            name, ext = os.path.splitext(sanitized)
            max_name_len = FilenameValidator.MAX_LENGTH - len(ext)
            sanitized = name[:max_name_len] + ext

        # Ensure not empty
        if not sanitized:
            sanitized = "unnamed"

        return sanitized

    @staticmethod
    def validate_filename(filename: str) -> bool:
        """
        Check if filename is valid.

        Args:
            filename: Filename to validate

        Returns:
            True if valid, False otherwise
        """
        if not filename or filename in ('.', '..'):
            return False

        if re.search(FilenameValidator.INVALID_CHARS, filename):
            return False

        if len(filename) > FilenameValidator.MAX_LENGTH:
            return False

        return True


class ConfigValidator:
    """Validates configuration dictionaries."""

    @staticmethod
    def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
        """
        Validate configuration against a schema.

        Args:
            config: Configuration dictionary
            schema: Schema dictionary with required keys and types

        Raises:
            ValidationError: If configuration is invalid
        """
        for key, expected_type in schema.items():
            if key not in config:
                raise ValidationError(f"Missing required config key: {key}")

            if not isinstance(config[key], expected_type):
                raise ValidationError(
                    f"Invalid type for {key}: expected {expected_type.__name__}, "
                    f"got {type(config[key]).__name__}"
                )

    @staticmethod
    def validate_api_config(config: Dict[str, Any]) -> None:
        """
        Validate API configuration.

        Args:
            config: API configuration dictionary

        Raises:
            ValidationError: If configuration is invalid
        """
        required = {
            'provider': str,
            'base_url': str,
            'model_name': str,
        }

        ConfigValidator.validate_config(config, required)

        # Validate provider
        valid_providers = ['openai', 'ollama', 'localai', 'custom']
        if config['provider'] not in valid_providers:
            raise ValidationError(
                f"Invalid provider: {config['provider']}. "
                f"Must be one of: {', '.join(valid_providers)}"
            )

        # Validate numeric values if present
        if 'temperature' in config:
            temp = config['temperature']
            if not isinstance(temp, (int, float)) or not 0 <= temp <= 2:
                raise ValidationError("Temperature must be between 0 and 2")

        if 'max_tokens' in config:
            max_tokens = config['max_tokens']
            if not isinstance(max_tokens, int) or max_tokens <= 0:
                raise ValidationError("max_tokens must be a positive integer")


class JSONResponseValidator:
    """Validates JSON responses from LLM."""

    @staticmethod
    def validate_classification_response(data: Dict[str, Any]) -> None:
        """
        Validate classification response from LLM.

        Args:
            data: Response data dictionary

        Raises:
            ValidationError: If response is invalid
        """
        required_fields = ['primary_category', 'confidence']

        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate primary_category
        if not isinstance(data['primary_category'], str) or not data['primary_category']:
            raise ValidationError("primary_category must be a non-empty string")

        # Validate confidence
        confidence = data['confidence']
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValidationError("confidence must be a number between 0 and 1")

        # Validate optional fields
        for field in ['subcategory', 'sub_subcategory', 'reasoning']:
            if field in data and data[field] is not None:
                if not isinstance(data[field], str):
                    raise ValidationError(f"{field} must be a string or null")
