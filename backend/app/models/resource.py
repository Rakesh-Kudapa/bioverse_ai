from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BinaryResource:
    """Validated binary content fetched from an approved source."""

    content: bytes
    media_type: str
    filename: str
