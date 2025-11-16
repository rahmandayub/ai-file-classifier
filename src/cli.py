"""Command-line interface for the AI File Classifier."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .app_controller import ApplicationController
from .utils.config_manager import load_config, get_config
from .utils.logger import configure_logger, get_logger
from .utils.validators import PathValidator
from .utils.exceptions import ClassifierError, ConfigurationError, ValidationError


def normalize_language_code(language: str) -> str:
    """
    Normalize language code to full language name.

    Args:
        language: Language code or full name

    Returns:
        Normalized language name
    """
    language_map = {
        'id': 'indonesian',
        'indonesian': 'indonesian',
        'en': 'english',
        'english': 'english',
        'es': 'spanish',
        'spanish': 'spanish',
        'fr': 'french',
        'french': 'french',
        'de': 'german',
        'german': 'german',
        'ja': 'japanese',
        'japanese': 'japanese',
        'zh': 'chinese',
        'chinese': 'chinese'
    }

    normalized = language_map.get(language.lower())
    if not normalized:
        raise ValidationError(
            f"Unsupported language: {language}. "
            f"Supported: id/indonesian, en/english, es/spanish, fr/french, de/german, ja/japanese, zh/chinese"
        )
    return normalized


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure argument parser.

    Returns:
        Configured ArgumentParser
    """
    parser = argparse.ArgumentParser(
        description="AI File Classifier - Automatically organize files using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Classify files in current directory
  %(prog)s classify . ./organized

  # Dry run to preview changes
  %(prog)s classify ./files ./organized --dry-run

  # Use Indonesian for directory names
  %(prog)s classify ./files ./organized --language id

  # Use English for directory names
  %(prog)s classify ./files ./organized --language en

  # Use custom configuration
  %(prog)s classify ./files ./organized --config config.yaml

  # Set verbose logging
  %(prog)s classify ./files ./organized --verbose

For more information, visit: https://github.com/yourusername/ai-file-classifier
        """
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Classify command
    classify_parser = subparsers.add_parser(
        'classify',
        help='Classify and organize files'
    )

    classify_parser.add_argument(
        'source',
        type=str,
        help='Source directory to scan'
    )

    classify_parser.add_argument(
        'destination',
        type=str,
        help='Destination directory for organized files'
    )

    classify_parser.add_argument(
        '--config',
        '-c',
        type=str,
        help='Path to configuration file (YAML)'
    )

    classify_parser.add_argument(
        '--dry-run',
        '-d',
        action='store_true',
        help='Preview changes without executing'
    )

    classify_parser.add_argument(
        '--no-report',
        action='store_true',
        help='Skip report generation'
    )

    classify_parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )

    classify_parser.add_argument(
        '--quiet',
        '-q',
        action='store_true',
        help='Suppress non-error output'
    )

    classify_parser.add_argument(
        '--language',
        '-l',
        type=str,
        default=None,
        help='Language for directory names (id/indonesian, en/english, es/spanish, fr/french, de/german, ja/japanese, zh/chinese). Default: english'
    )

    return parser


class CLIApp:
    """Command-line application for AI File Classifier."""

    def __init__(self):
        """Initialize CLI application."""
        self.parser = create_parser()
        self.logger = None

    def run(self, args: Optional[list] = None) -> int:
        """
        Run the CLI application.

        Args:
            args: Command-line arguments (None = sys.argv)

        Returns:
            Exit code (0 = success, 1 = error)
        """
        try:
            # Parse arguments
            parsed_args = self.parser.parse_args(args)

            if not parsed_args.command:
                self.parser.print_help()
                return 1

            # Load configuration
            config = load_config(parsed_args.config)

            # Configure logging
            log_level = 'DEBUG' if getattr(parsed_args, 'verbose', False) else config['app']['log_level']
            if getattr(parsed_args, 'quiet', False):
                log_level = 'ERROR'

            configure_logger(
                level=log_level,
                log_file=config['app']['log_file'],
                log_rotation=config['app']['log_rotation'],
                max_log_size_mb=config['app']['max_log_size_mb']
            )

            self.logger = get_logger()

            # Execute command
            if parsed_args.command == 'classify':
                return self._classify_command(parsed_args, config)

            return 0

        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return 130

        except (ConfigurationError, ValidationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

        except ClassifierError as e:
            print(f"Classification error: {e}", file=sys.stderr)
            return 1

        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            if self.logger:
                self.logger.exception("Unexpected error occurred")
            return 1

    def _classify_command(self, args, config) -> int:
        """
        Execute classify command.

        Args:
            args: Parsed arguments
            config: Configuration dictionary

        Returns:
            Exit code
        """
        try:
            # Validate paths
            source_path = PathValidator.validate_directory(args.source, must_exist=True)
            dest_path = PathValidator.validate_path(args.destination, must_exist=False)

            # Create destination directory if it doesn't exist
            dest_path.mkdir(parents=True, exist_ok=True)

            # Apply CLI argument overrides to config
            if args.dry_run:
                config['preferences']['dry_run_default'] = True

            # Apply language override if specified
            if args.language:
                normalized_language = normalize_language_code(args.language)
                if 'language' not in config:
                    config['language'] = {}
                config['language']['primary'] = normalized_language
                self.logger.info(f"Using language from CLI: {normalized_language}")

            # Create application controller
            app = ApplicationController(config)

            # Execute classification
            result = app.execute(
                source_dir=source_path,
                dest_dir=dest_path,
                dry_run=args.dry_run,
                generate_report=not args.no_report
            )

            # Print summary
            if not args.quiet:
                self._print_summary(result, args.dry_run)

            return 0 if result['success'] else 1

        except ValidationError as e:
            self.logger.error(f"Validation error: {e}")
            return 1

        except ClassifierError as e:
            self.logger.error(f"Classification error: {e}")
            return 1

    def _print_summary(self, result: dict, dry_run: bool) -> None:
        """
        Print execution summary.

        Args:
            result: Execution result dictionary
            dry_run: Whether this was a dry run
        """
        mode = "DRY RUN" if dry_run else "EXECUTION"

        print("\n" + "="*60)
        print(f"CLASSIFICATION SUMMARY ({mode})")
        print("="*60)
        print(f"Total files:          {result['total_files']}")
        print(f"Successfully classified: {result['classified']}")
        print(f"Failed:               {result['failed']}")

        if result.get('operation_stats'):
            stats = result['operation_stats']
            print(f"\nFile operations:")
            print(f"  Success:  {stats.get('success', 0)}")
            print(f"  Failed:   {stats.get('failed', 0)}")
            print(f"  Skipped:  {stats.get('skipped', 0)}")

        print(f"\nExecution time: {result['execution_time']:.2f} seconds")

        if result.get('cache_stats'):
            cache = result['cache_stats']
            if cache['enabled']:
                print(f"\nCache statistics:")
                print(f"  Memory entries: {cache['memory_entries']}")
                print(f"  Disk entries:   {cache['disk_entries']}")
                print(f"  Total size:     {cache['total_size_mb']:.2f} MB")

        print("="*60)


def main():
    """Main entry point for CLI."""
    app = CLIApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()
