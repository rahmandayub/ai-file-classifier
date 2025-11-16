"""File information model."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    """Represents metadata and information about a file."""

    path: Path
    name: str
    extension: str
    size: int
    created: datetime
    modified: datetime
    content_preview: Optional[str] = None
    mime_type: Optional[str] = None
    metadata: Optional[dict] = None

    def __hash__(self) -> int:
        """
        Hash based on file path for use as dictionary key.

        Returns:
            Hash value based on file path
        """
        return hash(self.path)

    def __eq__(self, other) -> bool:
        """
        Equality based on file path.

        Args:
            other: Another FileInfo object

        Returns:
            True if paths are equal
        """
        if not isinstance(other, FileInfo):
            return False
        return self.path == other.path

    @classmethod
    def from_path(cls, file_path: Path, read_content: bool = False, max_content_length: int = 5000) -> 'FileInfo':
        """
        Create FileInfo from a file path.

        Args:
            file_path: Path to the file
            read_content: Whether to read file content preview
            max_content_length: Maximum content length to read

        Returns:
            FileInfo instance
        """
        stat = file_path.stat()

        # Get file name and extension
        name = file_path.name
        extension = file_path.suffix.lower()

        # Get timestamps
        created = datetime.fromtimestamp(stat.st_ctime)
        modified = datetime.fromtimestamp(stat.st_mtime)

        # Read content preview if requested and file is text-based
        content_preview = None
        if read_content and cls._is_text_file(extension):
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(max_content_length)
                    content_preview = content[:max_content_length]
            except (IOError, UnicodeDecodeError):
                # File might be binary or unreadable
                pass

        return cls(
            path=file_path,
            name=name,
            extension=extension,
            size=stat.st_size,
            created=created,
            modified=modified,
            content_preview=content_preview
        )

    @staticmethod
    def _is_text_file(extension: str) -> bool:
        """
        Check if file extension indicates a text file.

        Args:
            extension: File extension (with dot)

        Returns:
            True if likely a text file
        """
        text_extensions = {
            '.txt', '.md', '.py', '.js', '.java', '.cpp', '.c', '.h',
            '.html', '.css', '.json', '.xml', '.yaml', '.yml', '.toml',
            '.ini', '.cfg', '.conf', '.sh', '.bash', '.bat', '.ps1',
            '.sql', '.go', '.rs', '.rb', '.php', '.pl', '.r', '.m',
            '.swift', '.kt', '.ts', '.tsx', '.jsx', '.vue', '.scala',
            '.log', '.csv', '.tsv'
        }
        return extension in text_extensions

    @property
    def size_formatted(self) -> str:
        """
        Get human-readable file size.

        Returns:
            Formatted size string (e.g., "1.5 MB")
        """
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @property
    def created_date(self) -> str:
        """
        Get formatted creation date.

        Returns:
            Formatted date string
        """
        return self.created.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def modified_date(self) -> str:
        """
        Get formatted modification date.

        Returns:
            Formatted date string
        """
        return self.modified.strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary with file information
        """
        return {
            'path': str(self.path),
            'name': self.name,
            'extension': self.extension,
            'size': self.size,
            'size_formatted': self.size_formatted,
            'created': self.created_date,
            'modified': self.modified_date,
            'content_preview': self.content_preview[:200] if self.content_preview else None,
            'mime_type': self.mime_type,
            'metadata': self.metadata
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"FileInfo(name='{self.name}', size={self.size_formatted}, modified={self.modified_date})"
