"""Classification result model."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Classification:
    """Represents a classification result for a file."""

    path: List[str]
    confidence: float
    reasoning: str = ""
    strategy: str = "content_based"
    metadata: Optional[dict] = None

    @property
    def directory_path(self) -> str:
        """
        Get the full directory path as a string.

        Returns:
            Path components joined with forward slashes
        """
        return '/'.join(self.path)

    @property
    def primary_category(self) -> str:
        """
        Get the primary (top-level) category.

        Returns:
            Primary category name
        """
        return self.path[0] if self.path else ""

    @property
    def subcategory(self) -> Optional[str]:
        """
        Get the subcategory (second level).

        Returns:
            Subcategory name or None
        """
        return self.path[1] if len(self.path) > 1 else None

    @property
    def sub_subcategory(self) -> Optional[str]:
        """
        Get the sub-subcategory (third level).

        Returns:
            Sub-subcategory name or None
        """
        return self.path[2] if len(self.path) > 2 else None

    @property
    def depth(self) -> int:
        """
        Get the depth of the classification path.

        Returns:
            Number of path components
        """
        return len(self.path)

    def to_dict(self) -> dict:
        """
        Convert to dictionary representation.

        Returns:
            Dictionary with classification information
        """
        return {
            'primary_category': self.primary_category,
            'subcategory': self.subcategory,
            'sub_subcategory': self.sub_subcategory,
            'full_path': self.directory_path,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'strategy': self.strategy,
            'depth': self.depth,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Classification':
        """
        Create Classification from dictionary.

        Args:
            data: Dictionary with classification data

        Returns:
            Classification instance
        """
        # Build path components
        path = []
        if 'primary_category' in data:
            path.append(data['primary_category'])
        if data.get('subcategory'):
            path.append(data['subcategory'])
        if data.get('sub_subcategory'):
            path.append(data['sub_subcategory'])

        return cls(
            path=path,
            confidence=data.get('confidence', 0.0),
            reasoning=data.get('reasoning', ''),
            strategy=data.get('strategy', 'content_based'),
            metadata=data.get('metadata')
        )

    def __repr__(self) -> str:
        """String representation."""
        return f"Classification(path={self.directory_path}, confidence={self.confidence:.2f}, strategy={self.strategy})"
