from enum import StrEnum


class ErrorCode(StrEnum):
    ENTITY_NOT_FOUND = "ENTITY_NOT_FOUND"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    SOURCE_TIMEOUT = "SOURCE_TIMEOUT"
    SOURCE_RATE_LIMITED = "SOURCE_RATE_LIMITED"
    INVALID_EXTERNAL_PAYLOAD = "INVALID_EXTERNAL_PAYLOAD"
    STRUCTURE_NOT_AVAILABLE = "STRUCTURE_NOT_AVAILABLE"


class BioVerseError(Exception):
    """Base class for controlled, user-safe application failures."""

    code: ErrorCode
    status_code: int
    retryable: bool
    source: str | None

    def __init__(self, message: str, *, source: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.source = source


class EntityNotFoundError(BioVerseError):
    code = ErrorCode.ENTITY_NOT_FOUND
    status_code = 404
    retryable = False


class SourceUnavailableError(BioVerseError):
    code = ErrorCode.SOURCE_UNAVAILABLE
    status_code = 503
    retryable = True


class SourceTimeoutError(BioVerseError):
    code = ErrorCode.SOURCE_TIMEOUT
    status_code = 504
    retryable = True


class SourceRateLimitedError(BioVerseError):
    code = ErrorCode.SOURCE_RATE_LIMITED
    status_code = 503
    retryable = True


class InvalidExternalPayloadError(BioVerseError):
    code = ErrorCode.INVALID_EXTERNAL_PAYLOAD
    status_code = 502
    retryable = True


class StructureNotAvailableError(BioVerseError):
    code = ErrorCode.STRUCTURE_NOT_AVAILABLE
    status_code = 404
    retryable = False
