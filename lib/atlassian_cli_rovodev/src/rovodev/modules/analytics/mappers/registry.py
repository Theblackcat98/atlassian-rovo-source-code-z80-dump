"""Event mapper registry."""

from typing import Any, Dict, List, Optional

from loguru import logger

from .base import SpanEventMapper


class EventMapperRegistry:
    """Registry for event mappers."""

    def __init__(self):
        """Initialize the registry."""
        self._mappers: List[SpanEventMapper] = []

    def register_mapper(self, mapper: SpanEventMapper) -> None:
        """
        Register an event mapper.

        Args:
            mapper: The event mapper to register
        """
        self._mappers.append(mapper)
        logger.debug(f"Registered mapper: {mapper.__class__.__name__}")

    def get_mappers_for_span(self, span_dict: Dict[str, Any], is_start: bool) -> List[SpanEventMapper]:
        """
        Get all appropriate mappers for a span.

        Args:
            span_dict: Dictionary representation of the span
            is_start: Whether this is a start event (True) or end event (False)

        Returns:
            List[SpanEventMapper]: All mappers that can handle the span
        """
        matching_mappers = []
        for mapper in self._mappers:
            if mapper.can_map(span_dict, is_start):
                logger.debug(f"Found mapper {mapper.__class__.__name__} for span {span_dict.get('name', 'unknown')}")
                matching_mappers.append(mapper)

        if not matching_mappers:
            logger.debug(f"No mappers found for span {span_dict.get('name', 'unknown')}")

        return matching_mappers
