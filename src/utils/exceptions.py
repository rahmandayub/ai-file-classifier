"""Custom exceptions for the AI File Classifier."""


class ClassifierError(Exception):
    """Base exception for all classifier errors."""
    pass


class ClassificationError(ClassifierError):
    """Raised when file classification fails."""
    pass


class APIError(ClassifierError):
    """Raised when API calls fail."""
    pass


class FileOperationError(ClassifierError):
    """Raised when file operations fail."""
    pass


class ConfigurationError(ClassifierError):
    """Raised when configuration is invalid."""
    pass


class ValidationError(ClassifierError):
    """Raised when input validation fails."""
    pass


class CacheError(ClassifierError):
    """Raised when cache operations fail."""
    pass
