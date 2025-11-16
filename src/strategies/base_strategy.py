"""Base classification strategy."""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.file_info import FileInfo
from ..models.classification import Classification


class ClassificationStrategy(ABC):
    """Abstract base class for classification strategies."""

    def __init__(self, name: str, weight: float = 1.0):
        """
        Initialize strategy.

        Args:
            name: Strategy name
            weight: Strategy weight for hybrid classification
        """
        self.name = name
        self.weight = weight

    @abstractmethod
    def classify(self, file_info: FileInfo) -> Optional[Classification]:
        """
        Classify a file.

        Args:
            file_info: File information object

        Returns:
            Classification result or None if strategy cannot classify
        """
        pass

    @abstractmethod
    def can_handle(self, file_info: FileInfo) -> bool:
        """
        Check if strategy can handle this file type.

        Args:
            file_info: File information object

        Returns:
            True if strategy can handle this file
        """
        pass

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(name='{self.name}', weight={self.weight})"
