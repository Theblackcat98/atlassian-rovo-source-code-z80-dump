"""Event mapper for application crash events."""

from typing import Any, Dict, Optional

from ..user_info import get_user_and_tenant_info
from .base import SpanEventMapper


class CrashEventMapper(SpanEventMapper):
    """Maps application crash spans to analytics events."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this mapper can handle the span."""
        name = span_dict.get("name", "")
        return name == "Application crash"

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map crash span to analytics event."""
        if is_start:
            return None  # Only track completed crash events

        # Track crash analytics for all users (internal and external)
        # Logfire's built-in scrubbing will handle sensitive data privacy
        attributes = span_dict.get("attributes", {})

        # Common attributes (includes session_id automatically)
        event_attributes = self.get_common_attributes(span_dict)
        event_attributes.update(
            {
                "error_type": attributes.get("error_type", "unknown"),
                "error_message": attributes.get("error_message", ""),  # Logfire scrubbing handles privacy
                "command_context": attributes.get("command_context"),
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, is_start)),
                "isAIFeature": 0,  # Infrastructure event, not AI feature
            }
        )

        return {
            "source": "rovodev application crashed",
            "action": "crashed",
            "action_subject": "application",
            "attributes": event_attributes,
        }
