"""MCP event mapper."""

from typing import Any, Dict, Optional

from loguru import logger

from .base import SpanEventMapper


class MCPEventMapper(SpanEventMapper):
    """Maps MCP-related spans to Atlassian Analytics events."""

    def get_common_attributes(self, span_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Override common attributes for MCP events."""
        # Get base common attributes
        common_attrs = super().get_common_attributes(span_dict)

        # MCP events are not AI features
        common_attrs.update(
            {
                "isAIFeature": 0,
                "userGeneratedAI": 0,
            }
        )
        # Remove AI feature name for non-AI events
        common_attrs.pop("aiFeatureName", None)

        return common_attrs

    def can_map(self, span_dict: Dict[str, Any], is_start: bool) -> bool:
        """Check if this is an MCP-related span."""
        # Only map end events
        if is_start:
            return False

        name = span_dict.get("name", "")
        return name in ["mcp_server_startup", "mcp_server_shutdown"]

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map an MCP-related span to an Atlassian Analytics event."""
        # Don't map start events
        if is_start:
            return None

        attributes = span_dict.get("attributes", {})
        name = span_dict.get("name", "")

        # Log the event data for debugging
        logger.debug(f"Processing MCP event with attributes: {attributes}")

        # Get common attributes (with AI-related modifications)
        event_attributes = self.get_common_attributes(span_dict)

        # Add MCP-specific attributes
        event_attributes.update(
            {
                "server_type": attributes.get("server_type", "unknown"),
                "connection_info": attributes.get("connection_info", "unknown"),
                "timestamp": self.format_timestamp(self.get_span_timestamp(span_dict, is_start)),
            }
        )

        # Add completion attributes
        success = attributes.get("success", True)
        event_attributes["success"] = success

        if error := attributes.get("error"):
            event_attributes["error"] = error

        # Determine action based on success
        action = "error" if not success else "completed"

        # Determine source based on event type
        source = "rovodev mcp server startup" if name == "mcp_server_startup" else "rovodev mcp server shutdown"

        return {
            "source": source,
            "action": action,
            "action_subject": "mcp_server",
            "attributes": event_attributes,
        }
