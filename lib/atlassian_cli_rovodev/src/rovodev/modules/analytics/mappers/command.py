"""Command event mapper."""

from typing import Any, Dict, Optional

from loguru import logger

from .base import SpanEventMapper


class CommandEventMapper(SpanEventMapper):
    """Maps command-related spans to Atlassian Analytics events."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is a command-related span."""
        name = span_dict.get("name", "")
        return name == "command executed"

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map a command-related span to an Atlassian Analytics event."""
        # Extract relevant data from the span
        attributes = span_dict.get("attributes", {})

        # Log the event data for debugging
        logger.debug(f"Processing command event with attributes: {attributes}")

        # Extract command information
        command_name = attributes.get("command_name", "unknown")
        sub_command = attributes.get("sub_command")

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add command-specific attributes
        timestamp = self.get_span_timestamp(span_dict, is_start)
        event_attributes.update({"command": command_name, "timestamp": self.format_timestamp(timestamp)})

        # Add optional attributes
        if sub_command:
            event_attributes["sub_command"] = sub_command

        if is_start:
            # For start events, we just need the basic command info
            return {
                "source": "rovodev command started",
                "action": "started",
                "action_subject": "command",
                "attributes": event_attributes,
            }
        else:
            # For end events, we need to check success/failure and include additional data
            success = attributes.get("success", True)
            event_attributes["success"] = success

            # Add duration for completed events
            if "start_time" in span_dict and "end_time" in span_dict:
                duration_ms = self.calculate_duration_ms(span_dict["start_time"], span_dict["end_time"])
                event_attributes["duration_ms"] = duration_ms

            if not success:
                # Handle error case
                error = attributes.get("error")
                if error:
                    event_attributes["error"] = error
                return {
                    "source": "rovodev command error",
                    "action": "error",
                    "action_subject": "command",
                    "attributes": event_attributes,
                }
            else:
                # Handle success case
                return {
                    "source": "rovodev command completed",
                    "action": "completed",
                    "action_subject": "command",
                    "attributes": event_attributes,
                }
