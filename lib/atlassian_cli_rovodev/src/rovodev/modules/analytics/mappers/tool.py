"""Tool event mapper."""

import json
from typing import Any, Dict, Optional

from loguru import logger

from .base import SpanEventMapper


class ToolEventMapper(SpanEventMapper):
    """Maps tool-related spans to Atlassian Analytics events."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is a tool-related span."""
        name = span_dict.get("name", "")
        attributes = span_dict.get("attributes", {})

        return "running tool" in name and "gen_ai.tool.name" in attributes

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map a tool-related span to an Atlassian Analytics event."""
        # Extract relevant data from the span
        attributes = span_dict.get("attributes", {})

        # Log the event data for debugging
        logger.debug(f"Processing tool event with attributes: {attributes}")

        # Extract tool information
        tool_name = attributes.get("gen_ai.tool.name", "unknown")
        tool_call_id = attributes.get("gen_ai.tool.call.id", "unknown")

        # Check for error status
        status = span_dict.get("status", {}).get("status_code", "UNSET")
        if status == "ERROR":
            return self._map_error_event(span_dict, tool_name, tool_call_id)

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add tool-specific attributes
        event_attributes.update(
            {
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, is_start)),
            }
        )

        # Add timing information for completed events
        if not is_start:
            start_time = attributes.get("start_time", span_dict.get("start_time"))
            end_time = attributes.get("end_time", span_dict.get("end_time"))
            if start_time and end_time:
                duration_ms = self.calculate_duration_ms(start_time, end_time)
                event_attributes["duration_ms"] = duration_ms
            event_attributes["success"] = True  # Assuming success if we got an end event

        # Return the mapped event
        if is_start:
            return {
                "source": "rovodev tool started",
                "action": "started",
                "action_subject": "llm_tool_call",
                "attributes": event_attributes,
            }
        else:
            return {
                "source": "rovodev tool completed",
                "action": "completed",
                "action_subject": "llm_tool_call",
                "attributes": event_attributes,
            }

    def _map_error_event(self, span_dict: Dict[str, Any], tool_name: str, tool_call_id: str) -> Dict[str, Any]:
        """Map a tool error span to an Atlassian Analytics event."""
        attributes = span_dict.get("attributes", {})

        # Extract error information
        error_type = attributes.get("error.type", "unknown")
        error_message = attributes.get("error.message", "Unknown error")

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add tool-specific attributes
        event_attributes.update(
            {
                "tool_name": tool_name,
                "tool_call_id": tool_call_id,
                "error_type": error_type,
                "error_message": error_message,
                "success": False,
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, False)),
            }
        )

        # Return the mapped event
        return {
            "source": "rovodev tool error",
            "action": "error",
            "action_subject": "llm_tool_call",
            "attributes": event_attributes,
        }
