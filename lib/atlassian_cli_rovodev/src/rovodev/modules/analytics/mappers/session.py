"""Session event mapper."""

from typing import Any, Dict, Optional

from loguru import logger

from .base import SpanEventMapper


class SessionEventMapper(SpanEventMapper):
    """Maps session-related spans to Atlassian Analytics events."""

    def get_common_attributes(self, span_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Override common attributes for session events."""
        # Get base common attributes
        common_attrs = super().get_common_attributes(span_dict)

        # Modify only the AI-related attributes for session events
        common_attrs.update(
            {
                "isAIFeature": 0,  # Session events are not AI features
                "userGeneratedAI": 0,  # Session events are not AI-generated
            }
        )
        # Remove AI feature name for non-AI events
        common_attrs.pop("aiFeatureName", None)

        return common_attrs

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is a session-related span."""
        # Only map end events for sessions
        if is_start:
            logger.debug(f"Ignoring start event for session span: {span_dict.get('name', '')}")
            return False

        name = span_dict.get("name", "")
        can_map = name in [
            "session created",
            "session switched",
            "session restored",
            "session forked",
            "session deleted",
        ]

        if not can_map:
            logger.debug(f"Cannot map session span: name='{name}'")
        else:
            logger.debug(f"Can map session span: name='{name}'")

        return can_map

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map a session-related span to an Atlassian Analytics event."""
        # Don't map start events
        if is_start:
            return None

        # Extract event type from span name (e.g., "session created" -> "created")
        name = span_dict.get("name", "")
        event_type = name.split(" ", 1)[1]  # Get everything after "session "
        attributes = span_dict.get("attributes", {})

        # Get common attributes (with AI-related modifications)
        event_attributes = self.get_common_attributes(span_dict)

        # Override sessionId with current_session_id or deleted_session_id
        if "current_session_id" in attributes:
            event_attributes["sessionId"] = attributes["current_session_id"]
            event_attributes["singleInstrumentationID"] = attributes["current_session_id"]
        elif "deleted_session_id" in attributes:
            event_attributes["sessionId"] = attributes["deleted_session_id"]
            event_attributes["singleInstrumentationID"] = attributes["deleted_session_id"]

        # Add event-specific attributes based on event type
        if event_type == "switched":
            event_attributes["previous_session_id"] = attributes.get("previous_session_id")
        elif event_type == "forked":
            event_attributes["parent_session_id"] = attributes.get("parent_session_id")
        elif event_type == "restored":
            if "num_messages" in attributes:
                event_attributes["num_messages"] = attributes["num_messages"]
        elif event_type == "deleted":
            event_attributes["deleted_session_id"] = attributes.get("deleted_session_id")

        if "session_title" in attributes:
            event_attributes["session_title"] = attributes["session_title"]

        # Add timestamp
        timestamp = self.get_span_timestamp(span_dict, is_start)
        event_attributes["timestamp"] = self.format_timestamp(timestamp)

        return {
            "source": f"rovodev session {event_type}",
            "action": event_type,
            "action_subject": self.get_prefixed_action_subject("llm_session"),
            "attributes": event_attributes,
        }
