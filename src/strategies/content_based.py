"""Content-based classification strategy using AI."""

from typing import Optional

from .base_strategy import ClassificationStrategy
from ..models.file_info import FileInfo
from ..models.classification import Classification
from ..core.ai_classifier import AIClassifier


class ContentBasedStrategy(ClassificationStrategy):
    """Classifies files based on content analysis using AI."""

    def __init__(
        self,
        ai_classifier: AIClassifier,
        weight: float = 1.0
    ):
        """
        Initialize content-based strategy.

        Args:
            ai_classifier: AI classifier instance
            weight: Strategy weight
        """
        super().__init__(name="content_based", weight=weight)
        self.ai_classifier = ai_classifier

    def can_handle(self, file_info: FileInfo) -> bool:
        """
        Content-based strategy can handle any file.

        Args:
            file_info: File information object

        Returns:
            Always True
        """
        return True

    def classify(self, file_info: FileInfo) -> Optional[Classification]:
        """
        Classify file using AI analysis.

        Args:
            file_info: File information object

        Returns:
            Classification result or None if failed
        """
        classification = self.ai_classifier.classify(file_info)

        if classification:
            classification.strategy = self.name

        return classification
