"""Configuration management for the AI File Classifier."""

import os
import re
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from .exceptions import ConfigurationError
from .validators import ConfigValidator
from .logger import get_logger

logger = get_logger()


class ConfigManager:
    """Manages application configuration."""

    _instance: Optional['ConfigManager'] = None
    _config: Optional[Dict[str, Any]] = None

    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the configuration manager."""
        pass

    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file or use defaults.

        Args:
            config_path: Path to configuration file (YAML)

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If config cannot be loaded
        """
        if config_path:
            try:
                config_file = Path(config_path)
                if not config_file.exists():
                    raise ConfigurationError(f"Config file not found: {config_path}")

                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)

                logger.info(f"Loaded configuration from {config_path}")
            except yaml.YAMLError as e:
                raise ConfigurationError(f"Invalid YAML in config file: {e}")
            except Exception as e:
                raise ConfigurationError(f"Failed to load config: {e}")
        else:
            # Use default configuration
            config = self._get_default_config()
            logger.info("Using default configuration")

        # Expand environment variables
        config = self._expand_env_vars(config)

        # Validate configuration
        self._validate_config(config)

        self._config = config
        return config

    def get_config(self) -> Dict[str, Any]:
        """
        Get current configuration.

        Returns:
            Configuration dictionary

        Raises:
            ConfigurationError: If config not loaded
        """
        if self._config is None:
            raise ConfigurationError("Configuration not loaded. Call load_config() first.")
        return self._config

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key path.

        Args:
            key_path: Dot-separated key path (e.g., 'api.model_name')
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if self._config is None:
            return default

        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def _get_default_config(self) -> Dict[str, Any]:
        """
        Get default configuration.

        Returns:
            Default configuration dictionary
        """
        return {
            'app': {
                'name': 'AI File Classifier',
                'version': '1.0.0',
                'log_level': 'INFO',
                'log_file': 'logs/classifier.log',
                'log_rotation': True,
                'max_log_size_mb': 10,
                'cache_enabled': True,
                'cache_dir': '.cache',
                'cache_ttl_hours': 24,
            },
            'api': {
                'provider': 'ollama',
                'api_key': os.getenv('OPENAI_API_KEY', 'ollama'),
                'base_url': 'http://localhost:11434/v1',
                'model_name': 'llama3.2',
                'temperature': 0.2,
                'max_tokens': 1000,
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 2,
                'max_concurrent_requests': 5,
                'requests_per_minute': 60,
            },
            'classification': {
                'default_strategy': 'content_based',
                'confidence_threshold': 0.5,
                'fallback_strategy': 'heuristic',
                'max_depth': 3,
                'strategies': {
                    'content_based': {
                        'enabled': True,
                        'weight': 1.0,
                    },
                    'project_based': {
                        'enabled': True,
                        'weight': 0.8,
                        'project_indicators': ['README', 'package.json', '.git'],
                    },
                    'date_based': {
                        'enabled': False,
                        'format': 'YYYY/MM',
                    },
                    'type_based': {
                        'enabled': True,
                        'weight': 0.6,
                    },
                },
            },
            'scanning': {
                'recursive': True,
                'follow_symlinks': False,
                'max_depth': None,
                'ignore_hidden': True,
                'ignore_patterns': [
                    'node_modules',
                    '.git',
                    '__pycache__',
                    '*.tmp',
                    '.DS_Store',
                ],
                'file_filters': {
                    'extensions': {
                        'include': [],
                        'exclude': ['.exe', '.dll', '.so'],
                    },
                    'size': {
                        'min_bytes': 0,
                        'max_bytes': 104857600,  # 100 MB
                    },
                    'date': {
                        'modified_after': None,
                        'modified_before': None,
                    },
                },
            },
            'directories': {
                'naming_convention': 'snake_case',
                'sanitize_names': True,
                'max_name_length': 100,
                'conflict_resolution': 'append_counter',
                'create_index_files': False,
            },
            'operations': {
                'mode': 'move',
                'preserve_metadata': True,
                'preserve_permissions': True,
                'atomic_operations': True,
                'verify_after_move': True,
                'duplicate_handling': 'rename',
                'rename_pattern': '{name}_{counter}{ext}',
                'backup': {
                    'enabled': False,
                    'backup_dir': '.backup',
                    'keep_days': 7,
                },
            },
            'performance': {
                'batch_size': 50,
                'max_workers': 10,
                'max_memory_mb': 500,
                'enable_profiling': False,
                'content_analysis': {
                    'max_file_size_mb': 1,
                    'read_chunk_size_kb': 64,
                    'max_content_length': 5000,
                },
            },
            'reporting': {
                'enabled': True,
                'output_dir': 'reports',
                'formats': ['json', 'csv', 'html'],
                'include_details': True,
                'include_statistics': True,
                'include_errors': True,
            },
            'extensions': {
                'enabled': True,
                'plugin_directory': './plugins',
                'auto_load': True,
            },
            'preferences': {
                'interactive_mode': False,
                'confirm_before_execute': True,
                'show_progress': True,
                'dry_run_default': False,
                'verbose': False,
            },
        }

    def _expand_env_vars(self, config: Any) -> Any:
        """
        Recursively expand environment variables in configuration.

        Args:
            config: Configuration value (dict, list, or primitive)

        Returns:
            Configuration with expanded variables
        """
        if isinstance(config, dict):
            return {k: self._expand_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._expand_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Expand ${VAR_NAME} or $VAR_NAME patterns
            def replace_env_var(match):
                var_name = match.group(1) or match.group(2)
                return os.getenv(var_name, match.group(0))

            pattern = r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)'
            return re.sub(pattern, replace_env_var, config)
        else:
            return config

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """
        Validate configuration structure and values.

        Args:
            config: Configuration dictionary

        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            # Validate API configuration
            if 'api' in config:
                ConfigValidator.validate_api_config(config['api'])

            # Validate app configuration
            if 'app' in config:
                required_app = {
                    'name': str,
                    'version': str,
                    'log_level': str,
                }
                ConfigValidator.validate_config(config['app'], required_app)

        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {e}")


# Global config manager instance
_config_manager = ConfigManager()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults.

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    return _config_manager.load_config(config_path)


def get_config() -> Dict[str, Any]:
    """
    Get current configuration.

    Returns:
        Configuration dictionary
    """
    return _config_manager.get_config()


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Get configuration value by key path.

    Args:
        key_path: Dot-separated key path
        default: Default value if not found

    Returns:
        Configuration value
    """
    return _config_manager.get(key_path, default)
