"""Permission event mapper for Atlassian Analytics."""

from typing import Any, Dict, Optional

from rovodev.modules.analytics.mappers.base import SpanEventMapper


class PermissionEventMapper(SpanEventMapper):
    """Maps permission events to Atlassian Analytics events."""

    def get_common_attributes(self, span_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Override common attributes for permission events."""
        # Get base common attributes
        common_attrs = super().get_common_attributes(span_dict)

        # Permission events are not AI features
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
        """Check if this is a permission-related span."""
        name = span_dict.get("name", "")
        return name == "Tool permission decision"

    def map_event(
        self, span_dict: Dict[str, Any], is_start: bool, span: Optional[Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Map a permission-related span to an Atlassian Analytics event."""
        # Extract relevant data from the span
        attributes = span_dict.get("attributes", {})

        # Get common attributes (with AI-related modifications)
        event_attributes = self.get_common_attributes(span_dict)

        # Add timestamp
        event_attributes["timestamp"] = self.format_timestamp(self.get_span_timestamp(span_dict, is_start))

        # Add specific permission attributes we care about
        event_attributes.update(
            {
                "tool_name": attributes.get("tool_name"),
                "decision": attributes.get("decision"),
                "source": attributes.get("source"),
                "scope": attributes.get("scope"),
                "command": attributes.get("command"),
                "is_compound_command": attributes.get("is_compound_command"),
                "pattern_used": attributes.get("pattern_used"),
            }
        )

        # Return the mapped event
        return {
            "source": "rovodev permission decision",
            "action": "decision",
            "action_subject": "tool_permission",
            "attributes": event_attributes,
        }
