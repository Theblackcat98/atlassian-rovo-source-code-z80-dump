"""Tests for the session event mapper."""

import pytest

from rovodev.modules.analytics.mappers.session import SessionEventMapper


class TestSessionEventMapper:
    """Tests for the SessionEventMapper class."""

    @pytest.fixture
    def mapper(self):
        """Create a SessionEventMapper instance."""
        return SessionEventMapper()

    def test_ignores_start_events(self, mapper):
        """Test that start events are ignored."""
        span_dict = {
            "name": "session created",
            "attributes": {
                "session_event_type": "created",
                "current_session_id": "test-session-id",
            },
        }
        # Should not map start events
        assert not mapper.can_map(span_dict, is_start=True)
        assert mapper.map_event(span_dict, is_start=True) is None

        # Should map end events
        assert mapper.can_map(span_dict, is_start=False)
        event = mapper.map_event(span_dict, is_start=False)
        assert event is not None
        assert event["action"] == "created"

    def test_ai_attributes_for_session_events(self, mapper):
        """Test that AI-related attributes are correctly modified for session events."""
        span_dict = {
            "name": "session created",
            "attributes": {
                "session_event_type": "created",
                "current_session_id": "test-session-id",
                "session_title": "Test Session",
            },
        }

        event = mapper.map_event(span_dict, is_start=False)

        assert event is not None
        # Verify AI-related attributes are modified
        assert event["attributes"]["isAIFeature"] == 0
        assert event["attributes"]["userGeneratedAI"] == 0
        assert "aiFeatureName" not in event["attributes"]

        # Verify other common attributes remain unchanged
        assert "sessionId" in event["attributes"]
        assert "singleInstrumentationID" in event["attributes"]
        assert "timestamp" in event["attributes"]

    def test_map_session_created_event(self, mapper):
        """Test mapping a session created event."""
        span_dict = {
            "name": "session created",
            "attributes": {
                "session_event_type": "created",
                "current_session_id": "test-session-id",
                "session_title": "Test Session",
            },
        }
        event = mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["source"] == "rovodev session created"
        assert event["action"] == "created"
        assert event["action_subject"] == "llm_session"
        assert event["attributes"]["sessionId"] == "test-session-id"
        assert event["attributes"]["session_title"] == "Test Session"

    def test_map_session_switched_event(self, mapper):
        """Test mapping a session switched event."""
        span_dict = {
            "name": "session switched",
            "attributes": {
                "session_event_type": "switched",
                "current_session_id": "new-session-id",
                "previous_session_id": "old-session-id",
            },
        }
        event = mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["source"] == "rovodev session switched"
        assert event["action"] == "switched"
        assert event["attributes"]["sessionId"] == "new-session-id"
        assert event["attributes"]["previous_session_id"] == "old-session-id"

    def test_map_session_restored_event(self, mapper):
        """Test mapping a session restored event."""
        span_dict = {
            "name": "session restored",
            "attributes": {
                "session_event_type": "restored",
                "current_session_id": "test-session-id",
                "session_title": "Test Session",
                "num_messages": 5,
            },
        }
        event = mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["source"] == "rovodev session restored"
        assert event["action"] == "restored"
        assert event["attributes"]["sessionId"] == "test-session-id"
        assert event["attributes"]["session_title"] == "Test Session"
        assert event["attributes"]["num_messages"] == 5

    def test_map_session_forked_event(self, mapper):
        """Test mapping a session forked event."""
        span_dict = {
            "name": "session forked",
            "attributes": {
                "session_event_type": "forked",
                "current_session_id": "new-session-id",
                "parent_session_id": "parent-session-id",
                "session_title": "Forked Session",
            },
        }
        event = mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["source"] == "rovodev session forked"
        assert event["action"] == "forked"
        assert event["attributes"]["sessionId"] == "new-session-id"
        assert event["attributes"]["parent_session_id"] == "parent-session-id"
        assert event["attributes"]["session_title"] == "Forked Session"

    def test_map_session_deleted_event(self, mapper):
        """Test mapping a session deleted event."""
        span_dict = {
            "name": "session deleted",
            "attributes": {
                "session_event_type": "deleted",
                "deleted_session_id": "deleted-session-id",
                "session_title": "Deleted Session",
            },
        }
        event = mapper.map_event(span_dict, is_start=False)

        assert event is not None
        assert event["source"] == "rovodev session deleted"
        assert event["action"] == "deleted"
        assert event["action_subject"] == "llm_session"
        assert event["attributes"]["sessionId"] == "deleted-session-id"
        assert event["attributes"]["deleted_session_id"] == "deleted-session-id"
        assert event["attributes"]["session_title"] == "Deleted Session"
