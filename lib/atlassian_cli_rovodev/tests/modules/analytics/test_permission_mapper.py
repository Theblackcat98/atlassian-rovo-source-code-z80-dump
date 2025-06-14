"""Tests for the permission event mapper."""

import pytest

from rovodev.modules.analytics.mappers.permission import PermissionEventMapper


class TestPermissionEventMapper:
    """Tests for the permission event mapper."""

    def test_can_map(self):
        """Test that the mapper can identify permission events."""
        mapper = PermissionEventMapper()

        # Permission decision event (exact match)
        permission_span = {
            "name": "Tool permission decision",
            "attributes": {
                "tool_name": "bash",
                "command": "ls -la",
                "decision": "allow",
                "scope": "session",
                "source": "user_decision",
                "_tags": ["permission"],
            },
        }
        assert mapper.can_map(permission_span, is_start=False)

        # Non-permission event
        non_permission_span = {
            "name": "running tool",
            "attributes": {
                "gen_ai.tool.name": "bash",
                "gen_ai.tool.call.id": "call_123",
            },
        }
        assert not mapper.can_map(non_permission_span, is_start=False)

        # Different permission event name (should not match)
        other_permission_span = {
            "name": "Tool permission summary",
            "attributes": {
                "_tags": ["permission"],
            },
        }
        assert not mapper.can_map(other_permission_span, is_start=False)

    def test_map_decision_event(self):
        """Test mapping a permission decision event."""
        mapper = PermissionEventMapper()

        # Permission decision event
        permission_span = {
            "name": "Tool permission decision",
            "attributes": {
                "tool_name": "bash",
                "command": "ls -la",
                "decision": "allow",
                "scope": "session",
                "source": "user_decision",
                "is_compound_command": False,
                "pattern_used": False,
                "session_id": "test-session-123",
                "_tags": ["permission"],
            },
            "start_time": 1625097600000000000,  # Example timestamp
        }

        event = mapper.map_event(permission_span, is_start=False)

        assert event is not None
        assert event["source"] == "rovodev permission decision"
        assert event["action"] == "decision"
        assert event["action_subject"] == "tool_permission"
        assert event["attributes"]["tool_name"] == "bash"
        assert event["attributes"]["command"] == "ls -la"
        assert event["attributes"]["decision"] == "allow"
        assert event["attributes"]["scope"] == "session"
        assert event["attributes"]["source"] == "user_decision"
        assert event["attributes"]["is_compound_command"] is False
        assert event["attributes"]["pattern_used"] is False
        # session_id comes from base mapper's extract_session_id, not from span attributes
        assert "_tags" not in event["attributes"]  # Internal attributes should be excluded

        # Permission events are not AI features
        assert event["attributes"]["isAIFeature"] == 0
        assert event["attributes"]["userGeneratedAI"] == 0

    def test_unknown_event_type(self):
        """Test handling of unknown permission event types."""
        mapper = PermissionEventMapper()

        # Unknown permission event (different name)
        unknown_span = {
            "name": "Tool permission unknown",
            "attributes": {
                "_tags": ["permission"],
            },
        }

        # Should not be able to map this span
        can_map = mapper.can_map(unknown_span, is_start=False)
        assert can_map is False
