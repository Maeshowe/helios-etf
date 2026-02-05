"""
Exceptions for HELIOS ETF FLOW.

Provides a hierarchy of domain-specific exceptions
for clear error handling across the system.
"""


class HeliosError(Exception):
    """Base exception for all HELIOS errors."""


class ConfigurationError(HeliosError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, key: str | None = None) -> None:
        self.key = key
        super().__init__(message)


class DataFetchError(HeliosError):
    """Raised when an API request fails."""

    def __init__(
        self,
        message: str,
        source: str | None = None,
        status_code: int | None = None,
    ) -> None:
        self.source = source
        self.status_code = status_code
        super().__init__(message)


class InsufficientDataError(HeliosError):
    """Raised when there is not enough data for computation."""

    def __init__(
        self,
        message: str,
        feature: str | None = None,
        available: int | None = None,
        required: int | None = None,
    ) -> None:
        self.feature = feature
        self.available = available
        self.required = required
        super().__init__(message)


class NormalizationError(HeliosError):
    """Raised when normalization fails."""

    def __init__(self, message: str, feature: str | None = None) -> None:
        self.feature = feature
        super().__init__(message)


class RateLimitError(HeliosError):
    """Raised when API rate limit is exceeded."""

    def __init__(
        self,
        message: str,
        source: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        self.source = source
        self.retry_after = retry_after
        super().__init__(message)


class CacheError(HeliosError):
    """Raised when cache operations fail."""
