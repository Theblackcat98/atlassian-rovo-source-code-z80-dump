"""Tests for the crash event mapper."""

from unittest.mock import Mock, patch

import pytest

from rovodev.modules.analytics.mappers.crash import CrashEventMapper
from rovodev.modules.analytics.models import UserInfo


class TestCrashEventMapper:
    """Test cases for CrashEventMapper."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = CrashEventMapper()

    def test_can_map_crash_span(self):
        """Test that mapper can identify crash spans."""
        span_dict = {"name": "Application crash"}
        assert self.mapper.can_map(span_dict, is_start=False)

    def test_cannot_map_other_spans(self):
        """Test that mapper ignores non-crash spans."""
        span_dict = {"name": "Some other operation"}
        assert not self.mapper.can_map(span_dict, is_start=False)

    def test_map_crash_event_start_returns_none(self):
        """Test that start events return None (only track completed crashes)."""
        span_dict = {
            "name": "Application crash",
            "attributes": {
                "error_type": "ValueError",
                "error_message": "Test error",
                "session_id": "test-session-123",
                "command_context": "test command",
            },
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # Mock internal user
        internal_user = UserInfo(
            account_id="test-user", cloud_id="test-cloud", is_internal=True, user_type="atlassianAccount"
        )
        with patch("rovodev.modules.analytics.mappers.crash.get_user_and_tenant_info", return_value=internal_user):
            result = self.mapper.map_event(span_dict, is_start=True)
            assert result is None

    def test_map_crash_event_complete(self):
        """Test mapping a completed crash event."""
        span_dict = {
            "name": "Application crash",
            "attributes": {
                "error_type": "ValueError",
                "error_message": "Test error message",
                "command_context": "test command",
            },
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # Mock internal user
        internal_user = UserInfo(
            account_id="test-user", cloud_id="test-cloud", is_internal=True, user_type="atlassianAccount"
        )
        with patch("rovodev.modules.analytics.mappers.crash.get_user_and_tenant_info", return_value=internal_user):
            result = self.mapper.map_event(span_dict, is_start=False)

            assert result is not None
            assert result["source"] == "rovodev application crashed"
            assert result["action"] == "crashed"
            assert result["action_subject"] == "application"

            attributes = result["attributes"]
            assert attributes["error_type"] == "ValueError"
            assert attributes["error_message"] == "Test error message"
            assert attributes["command_context"] == "test command"
            assert attributes["isAIFeature"] == 0

    def test_map_crash_event_with_missing_attributes(self):
        """Test mapping crash event with missing optional attributes."""
        span_dict = {
            "name": "Application crash",
            "attributes": {
                "error_type": "RuntimeError",
            },
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # Mock internal user
        internal_user = UserInfo(
            account_id="test-user", cloud_id="test-cloud", is_internal=True, user_type="atlassianAccount"
        )
        with patch("rovodev.modules.analytics.mappers.crash.get_user_and_tenant_info", return_value=internal_user):
            result = self.mapper.map_event(span_dict, is_start=False)

            assert result is not None
            attributes = result["attributes"]
            assert attributes["error_type"] == "RuntimeError"
            assert attributes["error_message"] == ""  # Default for missing message
            assert attributes["command_context"] is None

    def test_external_users_get_crash_tracking(self):
        """Test that external users now get crash analytics events."""
        span_dict = {
            "name": "Application crash",
            "attributes": {
                "error_type": "ValueError",
                "error_message": "Test error message",
                "command_context": "test command",
            },
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # External users now get crash events (no need to mock user info since we don't check it)
        result = self.mapper.map_event(span_dict, is_start=False)

        assert result is not None  # External users now get events
        assert result["source"] == "rovodev application crashed"
        assert result["action"] == "crashed"
        assert result["action_subject"] == "application"

        attributes = result["attributes"]
        assert attributes["error_type"] == "ValueError"
        assert attributes["error_message"] == "Test error message"  # Logfire handles scrubbing
        assert attributes["command_context"] == "test command"
        assert attributes["isAIFeature"] == 0

    def test_crash_tracking_always_works(self):
        """Test that crash tracking works regardless of user info availability."""
        span_dict = {
            "name": "Application crash",
            "attributes": {
                "error_type": "ValueError",
                "error_message": "Test error message",
                "command_context": "test command",
            },
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # Should work regardless of user info (we don't check it anymore)
        result = self.mapper.map_event(span_dict, is_start=False)

        assert result is not None  # Always get event now
        attributes = result["attributes"]
        assert attributes["error_type"] == "ValueError"
        assert attributes["error_message"] == "Test error message"
        assert attributes["command_context"] == "test command"
        assert attributes["isAIFeature"] == 0
