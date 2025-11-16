"""File discovery and scanning module."""

import fnmatch
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set

from ..models.file_info import FileInfo
from ..utils.logger import get_logger
from ..utils.exceptions import ValidationError

logger = get_logger()


class FileFilter:
    """Configuration for file filtering."""

    def __init__(
        self,
        extensions_include: Optional[List[str]] = None,
        extensions_exclude: Optional[List[str]] = None,
        min_size: int = 0,
        max_size: Optional[int] = None,
        modified_after: Optional[datetime] = None,
        modified_before: Optional[datetime] = None
    ):
        """
        Initialize file filter configuration.

        Args:
            extensions_include: List of extensions to include (empty = all)
            extensions_exclude: List of extensions to exclude
            min_size: Minimum file size in bytes
            max_size: Maximum file size in bytes (None = no limit)
            modified_after: Only files modified after this date
            modified_before: Only files modified before this date
        """
        self.extensions_include = set(extensions_include or [])
        self.extensions_exclude = set(extensions_exclude or [])
        self.min_size = min_size
        self.max_size = max_size
        self.modified_after = modified_after
        self.modified_before = modified_before

    def matches(self, file_info: FileInfo) -> bool:
        """
        Check if file matches filter criteria.

        Args:
            file_info: File information object

        Returns:
            True if file matches all criteria
        """
        # Check extension include list
        if self.extensions_include and file_info.extension not in self.extensions_include:
            return False

        # Check extension exclude list
        if file_info.extension in self.extensions_exclude:
            return False

        # Check size constraints
        if file_info.size < self.min_size:
            return False

        if self.max_size is not None and file_info.size > self.max_size:
            return False

        # Check date constraints
        if self.modified_after and file_info.modified < self.modified_after:
            return False

        if self.modified_before and file_info.modified > self.modified_before:
            return False

        return True


class FileScanner:
    """Scans directories to discover files."""

    def __init__(
        self,
        recursive: bool = True,
        follow_symlinks: bool = False,
        ignore_hidden: bool = True,
        ignore_patterns: Optional[List[str]] = None,
        max_depth: Optional[int] = None
    ):
        """
        Initialize the file scanner.

        Args:
            recursive: Whether to scan subdirectories
            follow_symlinks: Whether to follow symbolic links
            ignore_hidden: Whether to ignore hidden files/directories
            ignore_patterns: List of patterns to ignore (e.g., 'node_modules', '*.tmp')
            max_depth: Maximum directory depth to scan (None = unlimited)
        """
        self.recursive = recursive
        self.follow_symlinks = follow_symlinks
        self.ignore_hidden = ignore_hidden
        self.ignore_patterns = ignore_patterns or []
        self.max_depth = max_depth

    def scan(
        self,
        path: Path,
        file_filter: Optional[FileFilter] = None,
        read_content: bool = False,
        max_content_length: int = 5000
    ) -> List[FileInfo]:
        """
        Scan directory and return list of files.

        Args:
            path: Directory path to scan
            file_filter: Optional file filter
            read_content: Whether to read file content previews
            max_content_length: Maximum content length to read

        Returns:
            List of FileInfo objects

        Raises:
            ValidationError: If path is invalid
        """
        if not path.exists():
            raise ValidationError(f"Path does not exist: {path}")

        if not path.is_dir():
            raise ValidationError(f"Path is not a directory: {path}")

        logger.info(f"Scanning directory: {path}")

        files = []
        self._scan_directory(
            path,
            files,
            file_filter,
            read_content,
            max_content_length,
            current_depth=0
        )

        logger.info(f"Found {len(files)} files")
        return files

    def _scan_directory(
        self,
        directory: Path,
        files: List[FileInfo],
        file_filter: Optional[FileFilter],
        read_content: bool,
        max_content_length: int,
        current_depth: int
    ) -> None:
        """
        Recursively scan directory (internal method).

        Args:
            directory: Directory to scan
            files: List to append discovered files to
            file_filter: Optional file filter
            read_content: Whether to read content
            max_content_length: Maximum content length
            current_depth: Current recursion depth
        """
        # Check depth limit
        if self.max_depth is not None and current_depth >= self.max_depth:
            return

        try:
            for entry in directory.iterdir():
                # Check if symlink (and whether to follow)
                if entry.is_symlink() and not self.follow_symlinks:
                    continue

                # Check if hidden
                if self.ignore_hidden and entry.name.startswith('.'):
                    continue

                # Check ignore patterns
                if self._should_ignore(entry.name):
                    continue

                # Process file
                if entry.is_file():
                    try:
                        file_info = FileInfo.from_path(
                            entry,
                            read_content=read_content,
                            max_content_length=max_content_length
                        )

                        # Apply filter
                        if file_filter is None or file_filter.matches(file_info):
                            files.append(file_info)
                            logger.debug(f"Added file: {file_info.name}")

                    except Exception as e:
                        logger.warning(f"Failed to process file {entry}: {e}")

                # Recurse into subdirectories
                elif entry.is_dir() and self.recursive:
                    # Check ignore patterns for directories
                    if self._should_ignore(entry.name):
                        logger.debug(f"Ignoring directory: {entry.name}")
                        continue

                    self._scan_directory(
                        entry,
                        files,
                        file_filter,
                        read_content,
                        max_content_length,
                        current_depth + 1
                    )

        except PermissionError:
            logger.warning(f"Permission denied: {directory}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

    def _should_ignore(self, name: str) -> bool:
        """
        Check if file/directory name matches ignore patterns.

        Args:
            name: File or directory name

        Returns:
            True if should be ignored
        """
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False

    def apply_filters(
        self,
        files: List[FileInfo],
        file_filter: FileFilter
    ) -> List[FileInfo]:
        """
        Apply filters to a list of files.

        Args:
            files: List of file information objects
            file_filter: Filter configuration

        Returns:
            Filtered list of files
        """
        filtered = [f for f in files if file_filter.matches(f)]
        logger.info(f"Filtered {len(files)} files to {len(filtered)} files")
        return filtered


def create_scanner_from_config(config: dict) -> FileScanner:
    """
    Create a FileScanner from configuration dictionary.

    Args:
        config: Scanning configuration

    Returns:
        FileScanner instance
    """
    return FileScanner(
        recursive=config.get('recursive', True),
        follow_symlinks=config.get('follow_symlinks', False),
        ignore_hidden=config.get('ignore_hidden', True),
        ignore_patterns=config.get('ignore_patterns', []),
        max_depth=config.get('max_depth')
    )


def create_filter_from_config(config: dict) -> FileFilter:
    """
    Create a FileFilter from configuration dictionary.

    Args:
        config: Filter configuration

    Returns:
        FileFilter instance
    """
    file_filters = config.get('file_filters', {})
    extensions = file_filters.get('extensions', {})
    size = file_filters.get('size', {})
    date = file_filters.get('date', {})

    return FileFilter(
        extensions_include=extensions.get('include', []),
        extensions_exclude=extensions.get('exclude', []),
        min_size=size.get('min_bytes', 0),
        max_size=size.get('max_bytes'),
        modified_after=date.get('modified_after'),
        modified_before=date.get('modified_before')
    )
