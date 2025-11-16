"""File moving and copying operations."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..models.file_info import FileInfo
from ..models.classification import Classification
from ..utils.logger import get_logger
from ..utils.exceptions import FileOperationError

logger = get_logger()


class DuplicateHandler:
    """Handles filename conflicts and duplicates."""

    @staticmethod
    def resolve_duplicate(
        destination: Path,
        strategy: str = "rename",
        rename_pattern: str = "{name}_{counter}{ext}"
    ) -> Path:
        """
        Resolve duplicate filename.

        Args:
            destination: Original destination path
            strategy: Resolution strategy (skip, rename, overwrite)
            rename_pattern: Pattern for renaming

        Returns:
            Resolved destination path
        """
        if not destination.exists():
            return destination

        if strategy == 'skip':
            logger.debug(f"Skipping duplicate: {destination.name}")
            return destination

        elif strategy == 'overwrite':
            logger.warning(f"Will overwrite: {destination.name}")
            return destination

        elif strategy == 'rename':
            return DuplicateHandler._generate_unique_name(
                destination,
                rename_pattern
            )

        else:
            # Default to rename
            return DuplicateHandler._generate_unique_name(
                destination,
                rename_pattern
            )

    @staticmethod
    def _generate_unique_name(
        destination: Path,
        pattern: str = "{name}_{counter}{ext}"
    ) -> Path:
        """
        Generate a unique filename.

        Args:
            destination: Original destination path
            pattern: Naming pattern

        Returns:
            Unique path
        """
        parent = destination.parent
        stem = destination.stem
        suffix = destination.suffix

        counter = 1
        while True:
            new_name = pattern.format(
                name=stem,
                counter=counter,
                ext=suffix
            )
            new_path = parent / new_name

            if not new_path.exists():
                logger.debug(f"Renamed to avoid conflict: {destination.name} -> {new_name}")
                return new_path

            counter += 1


class OperationLog:
    """Logs file operations for potential rollback."""

    def __init__(self):
        """Initialize operation log."""
        self.operations: List[Dict] = []

    def log_operation(
        self,
        operation_type: str,
        source: Path,
        destination: Path
    ) -> None:
        """
        Log a file operation.

        Args:
            operation_type: Type of operation (move, copy, create_dir)
            source: Source path
            destination: Destination path
        """
        self.operations.append({
            'type': operation_type,
            'source': str(source),
            'destination': str(destination),
            'timestamp': datetime.now().isoformat()
        })

    def rollback(self) -> None:
        """Reverse all logged operations."""
        logger.info("Initiating rollback...")

        for operation in reversed(self.operations):
            try:
                if operation['type'] == 'move':
                    # Move file back
                    dest_path = Path(operation['destination'])
                    src_path = Path(operation['source'])

                    if dest_path.exists():
                        shutil.move(str(dest_path), str(src_path))
                        logger.info(f"Rolled back: {dest_path} -> {src_path}")

                elif operation['type'] == 'copy':
                    # Delete copy
                    dest_path = Path(operation['destination'])
                    if dest_path.exists():
                        dest_path.unlink()
                        logger.info(f"Deleted copy: {dest_path}")

                elif operation['type'] == 'create_dir':
                    # Remove directory if empty
                    dest_path = Path(operation['destination'])
                    if dest_path.exists() and not any(dest_path.iterdir()):
                        dest_path.rmdir()
                        logger.info(f"Removed directory: {dest_path}")

            except Exception as e:
                logger.error(f"Rollback failed for {operation}: {e}")

        logger.info("Rollback complete")

    def get_operations(self) -> List[Dict]:
        """Get list of all operations."""
        return self.operations.copy()


class FileMover:
    """Executes file move and copy operations."""

    def __init__(
        self,
        mode: str = "move",
        preserve_metadata: bool = True,
        verify_after_move: bool = True,
        duplicate_handling: str = "rename",
        rename_pattern: str = "{name}_{counter}{ext}"
    ):
        """
        Initialize file mover.

        Args:
            mode: Operation mode (move or copy)
            preserve_metadata: Whether to preserve file metadata
            verify_after_move: Whether to verify file after operation
            duplicate_handling: How to handle duplicates
            rename_pattern: Pattern for renaming duplicates
        """
        self.mode = mode
        self.preserve_metadata = preserve_metadata
        self.verify_after_move = verify_after_move
        self.duplicate_handling = duplicate_handling
        self.rename_pattern = rename_pattern
        self.operation_log = OperationLog()

    def move_file(
        self,
        source: Path,
        destination: Path,
        dry_run: bool = False
    ) -> Tuple[bool, Optional[Path]]:
        """
        Move or copy a single file.

        Args:
            source: Source file path
            destination: Destination file path
            dry_run: If True, don't actually move files

        Returns:
            Tuple of (success, actual_destination_path)
        """
        if not source.exists():
            logger.error(f"Source file does not exist: {source}")
            return False, None

        # Resolve duplicates
        actual_destination = DuplicateHandler.resolve_duplicate(
            destination,
            self.duplicate_handling,
            self.rename_pattern
        )

        if dry_run:
            logger.info(
                f"[DRY RUN] Would {self.mode} {source.name} -> {actual_destination}"
            )
            return True, actual_destination

        try:
            # Ensure destination directory exists
            actual_destination.parent.mkdir(parents=True, exist_ok=True)

            # Perform operation
            if self.mode == 'move':
                shutil.move(str(source), str(actual_destination))
                logger.info(f"Moved: {source.name} -> {actual_destination}")
                self.operation_log.log_operation('move', source, actual_destination)

            elif self.mode == 'copy':
                shutil.copy2(str(source), str(actual_destination))
                logger.info(f"Copied: {source.name} -> {actual_destination}")
                self.operation_log.log_operation('copy', source, actual_destination)

            else:
                raise FileOperationError(f"Invalid mode: {self.mode}")

            # Verify operation
            if self.verify_after_move:
                if not actual_destination.exists():
                    raise FileOperationError(
                        f"Verification failed: {actual_destination} does not exist"
                    )

            return True, actual_destination

        except Exception as e:
            logger.error(f"Failed to {self.mode} {source.name}: {e}")
            raise FileOperationError(f"File operation failed: {e}")

    def move_batch(
        self,
        operations: List[Tuple[Path, Path]],
        dry_run: bool = False
    ) -> Dict[str, int]:
        """
        Execute batch file operations.

        Args:
            operations: List of (source, destination) tuples
            dry_run: If True, don't actually move files

        Returns:
            Statistics dictionary
        """
        stats = {
            'total': len(operations),
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

        for source, destination in operations:
            try:
                success, _ = self.move_file(source, destination, dry_run)
                if success:
                    stats['success'] += 1
                else:
                    stats['skipped'] += 1

            except FileOperationError as e:
                logger.error(f"Operation failed: {e}")
                stats['failed'] += 1

            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                stats['failed'] += 1

        logger.info(
            f"Batch operation complete: "
            f"{stats['success']} succeeded, "
            f"{stats['failed']} failed, "
            f"{stats['skipped']} skipped"
        )

        return stats

    def rollback(self) -> None:
        """Rollback all operations."""
        self.operation_log.rollback()

    def get_operation_log(self) -> List[Dict]:
        """
        Get operation log.

        Returns:
            List of operation dictionaries
        """
        return self.operation_log.get_operations()


def create_file_mover_from_config(config: dict) -> FileMover:
    """
    Create FileMover from configuration.

    Args:
        config: Operations configuration

    Returns:
        FileMover instance
    """
    return FileMover(
        mode=config.get('mode', 'move'),
        preserve_metadata=config.get('preserve_metadata', True),
        verify_after_move=config.get('verify_after_move', True),
        duplicate_handling=config.get('duplicate_handling', 'rename'),
        rename_pattern=config.get('rename_pattern', '{name}_{counter}{ext}')
    )
