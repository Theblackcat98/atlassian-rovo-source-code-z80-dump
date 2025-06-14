"""LLM event mapper."""

from typing import Any, Dict, Optional

from loguru import logger

from .base import SpanEventMapper


class LLMEventMapper(SpanEventMapper):
    """Maps LLM-related spans to Atlassian Analytics events."""

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is an LLM-related span."""
        name = span_dict.get("name", "")
        attributes = span_dict.get("attributes", {})

        return "chat" in name or (
            "gen_ai.operation.name" in attributes and attributes["gen_ai.operation.name"] == "chat"
        )

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map an LLM-related span to an Atlassian Analytics event."""
        # Extract relevant data from the span
        attributes = span_dict.get("attributes", {})

        # Log the event processing
        logger.debug("Processing LLM event")

        # Check for error status
        status = span_dict.get("status", {}).get("status_code", "UNSET")
        if status == "ERROR":
            return self._map_error_event(span_dict)

        # Determine action and source based on start/end
        if is_start:
            action = "started"
            source = "rovodev llm started"
        else:
            action = "completed"
            source = "rovodev llm completed"

        # Extract model ID
        model_id = attributes.get("gen_ai.request.model", "unknown")
        if not model_id or model_id == "unknown":
            # Try alternative attribute names
            model_id = attributes.get("model_id", "unknown")

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add LLM-specific attributes
        timestamp = self.get_span_timestamp(span_dict, is_start)
        event_attributes.update({"model_id": model_id, "timestamp": self.format_timestamp(timestamp)})

        # Add input tokens for start events
        if is_start:
            input_tokens = attributes.get("gen_ai.usage.input_tokens", 0)
            if not input_tokens:
                input_tokens = attributes.get("input_tokens", 0)
            event_attributes["input_tokens"] = input_tokens

        # Add token usage for completed events
        if not is_start:
            # Extract token counts
            input_tokens = attributes.get("gen_ai.usage.input_tokens", 0)
            if not input_tokens:
                input_tokens = attributes.get("input_tokens", 0)

            output_tokens = attributes.get("gen_ai.usage.output_tokens", 0)
            if not output_tokens:
                output_tokens = attributes.get("output_tokens", 0)

            # Calculate total tokens
            total_tokens = input_tokens + output_tokens

            event_attributes.update(
                {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens,
                }
            )

        # Add timing information for completed events
        if not is_start and "start_time" in span_dict and "end_time" in span_dict:
            duration_ms = self.calculate_duration_ms(span_dict["start_time"], span_dict["end_time"])
            event_attributes["duration_ms"] = duration_ms
            event_attributes["success"] = True  # Assuming success if we got an end event

        # Return the mapped event
        return {
            "source": source,
            "action": action,
            "action_subject": self.get_prefixed_action_subject("llm_call"),
            "attributes": event_attributes,
        }

    def _map_error_event(self, span_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Map an LLM error span to an Atlassian Analytics event."""
        attributes = span_dict.get("attributes", {})

        # Extract model ID
        model_id = attributes.get("gen_ai.request.model", "unknown")
        if not model_id or model_id == "unknown":
            # Try alternative attribute names
            model_id = attributes.get("model_id", "unknown")

        # Extract error information
        error_type = attributes.get("error.type", "unknown")
        error_message = attributes.get("error.message", "Unknown error")

        # Get common attributes
        event_attributes = self.get_common_attributes(span_dict)

        # Add LLM-specific attributes
        event_attributes.update(
            {
                "model_id": model_id,
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, False)),
            }
        )

        # Return the mapped event
        return {
            "source": "rovodev llm error",
            "action": "error",
            "action_subject": self.get_prefixed_action_subject("llm_call"),
            "attributes": event_attributes,
        }
