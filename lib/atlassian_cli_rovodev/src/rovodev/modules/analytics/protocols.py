"""Protocols for analytics interfaces."""

from typing import Any, Protocol


class SpanAttributeSetter(Protocol):
    """Protocol for setting span attributes."""

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute.

        Args:
            key: The attribute key
            value: The attribute value
        """
        pass
