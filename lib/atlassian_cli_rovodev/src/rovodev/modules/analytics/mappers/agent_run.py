"""Agent run event mapper."""

import json
from typing import Any, Dict, Optional

from loguru import logger

from .base import SpanEventMapper


class AgentRunEventMapper(SpanEventMapper):
    """Maps agent run spans to Atlassian Analytics events."""

    def __init__(self, collect_prompts: bool = False):
        """Initialize the mapper.

        Args:
            collect_prompts: Whether to collect prompts in analytics events.
        """
        self.collect_prompts = collect_prompts

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is an agent run span."""
        name = span_dict.get("name", "")
        return "agent run" in name

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map an agent run span to an Atlassian Analytics event."""
        # Extract relevant data from the span
        attributes = span_dict.get("attributes", {})

        # Check for error status
        status = span_dict.get("status", {}).get("status_code", "UNSET")
        if status == "ERROR":
            return self._map_error_event(span_dict)

        # Determine action and source based on start/end
        if is_start:
            action = "started"
            source = "rovodev agent started"
        else:
            action = "completed"
            source = "rovodev agent completed"

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add timestamp
        timestamp = self.get_span_timestamp(span_dict, is_start)
        event_attributes["timestamp"] = self.format_timestamp(timestamp)

        # Only include prompt if collection is enabled
        if self.collect_prompts:
            events_str = attributes.get("all_messages_events", "[]")
            try:
                events = json.loads(events_str)
                user_events = [e for e in events if e.get("role") == "user"]
                if user_events:
                    prompt = user_events[-1].get("content")
                    if prompt and not prompt.startswith("[Scrubbed"):
                        event_attributes["prompt"] = prompt
            except json.JSONDecodeError:
                logger.debug("Failed to parse events JSON")

        # Add duration for completed events
        if not is_start and "start_time" in span_dict and "end_time" in span_dict:
            duration_ms = self.calculate_duration_ms(span_dict["start_time"], span_dict["end_time"])
            event_attributes["duration_ms"] = duration_ms
            event_attributes["success"] = True

        return {
            "source": source,
            "action": action,
            "action_subject": self.get_prefixed_action_subject("agent_run"),
            "attributes": event_attributes,
        }

    def _map_error_event(self, span_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Map an error span to an Atlassian Analytics event."""
        attributes = span_dict.get("attributes", {})

        # Extract error information
        error_type = attributes.get("error.type", "unknown")
        error_message = attributes.get("error.message", "Unknown error")

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add error-specific attributes
        event_attributes.update(
            {
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, False)),
            }
        )

        # Only include prompt if collection is enabled
        if self.collect_prompts:
            events_str = attributes.get("all_messages_events", "[]")
            try:
                events = json.loads(events_str)
                user_events = [e for e in events if e.get("role") == "user"]
                if user_events:
                    prompt = user_events[-1].get("content")
                    if prompt and not prompt.startswith("[Scrubbed"):
                        event_attributes["prompt"] = prompt
            except json.JSONDecodeError:
                logger.debug("Failed to parse events JSON")

        return {
            "source": "rovodev agent error",
            "action": "error",
            "action_subject": self.get_prefixed_action_subject("agent_run"),
            "attributes": event_attributes,
        }
