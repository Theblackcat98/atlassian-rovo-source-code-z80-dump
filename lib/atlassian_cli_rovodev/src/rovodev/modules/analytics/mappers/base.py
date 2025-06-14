"""Base event mapper interface."""

import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from loguru import logger

from ..constants import ACTION_SUBJECT_PREFIX

# Constants for default values
DEFAULT_SESSION_ID = "00000000-0000-0000-0000-000000000000"
DEFAULT_AI_FEATURE_NAME = "Rovo Dev CLI"


class SpanEventMapper(ABC):
    """Interface for mapping OpenTelemetry spans to Atlassian Analytics events."""

    @abstractmethod
    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """
        Determine if this mapper can handle the given span.

        Args:
            span_dict: Dictionary representation of the span
            is_start: Whether this is a start event (True) or end event (False)

        Returns:
            bool: True if this mapper can handle the span, False otherwise
        """
        pass

    @abstractmethod
    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Map a span to an Atlassian Analytics event.

        Args:
            span_dict: Dictionary representation of the span
            is_start: Whether this is a start event (True) or end event (False)
            span: The actual span object (Span on start, ReadableSpan on end)

        Returns:
            Optional[Dict[str, Any]]: The mapped event, or None if the span should be ignored
        """
        pass

    def get_common_attributes(self, span_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get common attributes that should be included in all events.

        Args:
            span_dict: Dictionary representation of the span

        Returns:
            Dict[str, Any]: Common attributes
        """
        # Extract session ID from span or use default
        session_id = self.extract_session_id(span_dict)

        return {
            "sessionId": session_id,
            "isAIFeature": 1,
            "userGeneratedAI": 1,
            "aiFeatureName": DEFAULT_AI_FEATURE_NAME,
            "singleInstrumentationID": session_id,  # Use session ID as the instrumentation ID
            "start_time": self.format_timestamp(time.time_ns()),  # Current time in nanoseconds
        }

    def extract_session_id(self, span_dict: Dict[str, Any]) -> str:
        """Extract session ID from current context."""
        from ..instrumentation.session import CurrentSession

        current_session_id = CurrentSession.get_session_id()
        if not current_session_id:
            logger.warning("No current session ID found")
            return DEFAULT_SESSION_ID

        return current_session_id

    def get_span_timestamp(self, span_dict: Dict[str, Any], is_start: bool) -> int:
        """
        Get timestamp from span in nanoseconds.

        Args:
            span_dict: Dictionary representation of the span
            is_start: Whether to get start time (True) or end time (False)

        Returns:
            int: Timestamp in nanoseconds
        """
        if is_start:
            timestamp = span_dict.get("start_time")
        else:
            timestamp = span_dict.get("end_time")

        if timestamp is None:
            # Convert current time to nanoseconds
            return time.time_ns()

        if not isinstance(timestamp, int):
            logger.warning(f"Invalid timestamp format: {type(timestamp)}. Expected nanoseconds integer.")
            return time.time_ns()

        return timestamp

    def format_timestamp(self, nanos: int) -> str:
        """
        Convert nanosecond timestamp to ISO format with UTC timezone.

        Args:
            nanos: Timestamp in nanoseconds

        Returns:
            str: Timestamp in ISO format with UTC timezone (e.g., "2025-05-26T21:21:38.147398138Z")
        """
        seconds = nanos / 1_000_000_000
        dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")

    def get_prefixed_action_subject(self, action_subject: str) -> str:
        """
        Get the action subject with the standard prefix.

        Args:
            action_subject: The base action subject name (e.g., "llm", "tool")

        Returns:
            str: The prefixed action subject (e.g., "rovodev_llm")
        """
        return f"{ACTION_SUBJECT_PREFIX}{action_subject}"

    def calculate_duration_ms(self, start_time: int, end_time: int) -> int:
        """
        Calculate the duration in milliseconds between two nanosecond timestamps.

        Args:
            start_time: Start time in nanoseconds
            end_time: End time in nanoseconds

        Returns:
            int: The duration in milliseconds
        """
        try:
            duration_ns = end_time - start_time
            return int(duration_ns / 1_000_000)  # Convert ns to ms
        except (TypeError, ValueError) as e:
            logger.warning(f"Error calculating duration: {e}")
            return 0
