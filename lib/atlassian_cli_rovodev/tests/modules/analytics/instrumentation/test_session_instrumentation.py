"""Tests for session instrumentation."""

import unittest
from unittest.mock import MagicMock, patch

from rovodev.modules.analytics.instrumentation.session import (
    CurrentSession,
    track_session_created,
    track_session_deleted,
    track_session_forked,
    track_session_restored,
    track_session_switched,
)


class TestSessionInstrumentation(unittest.TestCase):
    def setUp(self):
        # Reset current session before each test
        CurrentSession.set_session_id(None)

    def test_current_session(self):
        """Test CurrentSession class."""
        # Initially no session
        self.assertIsNone(CurrentSession.get_session_id())

        # Set session
        CurrentSession.set_session_id("test-session")
        self.assertEqual(CurrentSession.get_session_id(), "test-session")

        # Clear session
        CurrentSession.set_session_id(None)
        self.assertIsNone(CurrentSession.get_session_id())

    @patch("logfire.span")
    def test_track_session_created(self, mock_span):
        """Test tracking session creation."""
        mock_context = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_context

        # Track session creation
        track_session_created("test-session-id", "Test Session")

        # Verify span attributes
        mock_context.set_attribute.assert_any_call("current_session_id", "test-session-id")
        mock_context.set_attribute.assert_any_call("session_event_type", "created")
        mock_context.set_attribute.assert_any_call("session_title", "Test Session")

        # Verify current session was updated
        self.assertEqual(CurrentSession.get_session_id(), "test-session-id")

    @patch("logfire.span")
    def test_track_session_switched(self, mock_span):
        """Test tracking session switching."""
        mock_context = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_context

        # Track session switch
        track_session_switched("old-session-id", "new-session-id")

        # Verify span attributes
        mock_context.set_attribute.assert_any_call("current_session_id", "new-session-id")
        mock_context.set_attribute.assert_any_call("session_event_type", "switched")
        mock_context.set_attribute.assert_any_call("previous_session_id", "old-session-id")

        # Verify current session was updated
        self.assertEqual(CurrentSession.get_session_id(), "new-session-id")

    @patch("logfire.span")
    def test_track_session_restored(self, mock_span):
        """Test tracking session restoration."""
        mock_context = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_context

        # Track session restoration
        track_session_restored("test-session-id", "Test Session", num_messages=5)

        # Verify span attributes
        mock_context.set_attribute.assert_any_call("current_session_id", "test-session-id")
        mock_context.set_attribute.assert_any_call("session_event_type", "restored")
        mock_context.set_attribute.assert_any_call("session_title", "Test Session")
        mock_context.set_attribute.assert_any_call("num_messages", 5)

        # Verify current session was updated
        self.assertEqual(CurrentSession.get_session_id(), "test-session-id")

    @patch("logfire.span")
    def test_track_session_forked(self, mock_span):
        """Test tracking session forking."""
        mock_context = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_context

        # Track session fork
        track_session_forked("parent-session-id", "child-session-id", "Forked Session")

        # Verify span attributes
        mock_context.set_attribute.assert_any_call("current_session_id", "child-session-id")
        mock_context.set_attribute.assert_any_call("session_event_type", "forked")
        mock_context.set_attribute.assert_any_call("parent_session_id", "parent-session-id")
        mock_context.set_attribute.assert_any_call("session_title", "Forked Session")

        # Verify current session was updated
        self.assertEqual(CurrentSession.get_session_id(), "child-session-id")

    @patch("logfire.span")
    def test_track_session_deleted(self, mock_span):
        """Test tracking session deletion."""
        mock_context = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_context

        # Track session deletion
        track_session_deleted("deleted-session-id", "Deleted Session")

        # Verify span attributes
        mock_context.set_attribute.assert_any_call("deleted_session_id", "deleted-session-id")
        mock_context.set_attribute.assert_any_call("session_event_type", "deleted")
        mock_context.set_attribute.assert_any_call("session_title", "Deleted Session")

        # Note: Current session should NOT be updated for deletion events
        # (the current session remains unchanged when deleting a different session)
