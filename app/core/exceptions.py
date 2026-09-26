from __future__ import annotations

"""Custom exceptions hierarchy for J.A.R.V.I.S. Mark V."""


class JarvisException(Exception):
    """Base exception for all J.A.R.V.I.S. errors."""

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(JarvisException):
    """Raised when environment variables or settings fail validation."""


class SecurityHardeningError(JarvisException):
    """Raised when security hardening checks or fail-fast routines fail."""


class LLMServiceError(JarvisException):
    """Raised when LLM invocation or parsing encounters a failure."""


class PersistenceError(JarvisException):
    """Raised during database or cache read/write failures (Mem0/Firestore)."""


class AuthenticationError(JarvisException):
    """Raised when authentication credentials or tokens are invalid."""
