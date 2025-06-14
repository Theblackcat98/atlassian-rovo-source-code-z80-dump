"""Tests for command event mapper."""

import unittest
from unittest.mock import MagicMock

from rovodev.modules.analytics.instrumentation.session import CurrentSession
from rovodev.modules.analytics.mappers.command import CommandEventMapper


class TestCommandEventMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = CommandEventMapper()
        # Reset current session before each test
        CurrentSession.set_session_id(None)

    def test_map_command_start_event(self):
        """Test mapping of command start events."""
        # Set current session
        CurrentSession.set_session_id("test-session")

        span_dict = {
            "name": "command executed",
            "attributes": {
                "command_name": "/sessions",
                "sub_command": "list",
            },
            "start_time": "2025-05-16T10:30:45.123Z",
        }

        event = self.mapper.map_event(span_dict, is_start=True)

        self.assertIsNotNone(event)
        self.assertEqual(event["source"], "rovodev command started")
        self.assertEqual(event["action"], "started")
        self.assertEqual(event["action_subject"], "command")
        self.assertEqual(event["attributes"]["command"], "/sessions")
        self.assertEqual(event["attributes"]["sub_command"], "list")
        self.assertEqual(event["attributes"]["sessionId"], "test-session")

    def test_map_command_complete_event(self):
        """Test mapping of command completion events."""
        # Set current session
        CurrentSession.set_session_id("test-session")

        span_dict = {
            "name": "command executed",
            "attributes": {
                "command_name": "/sessions",
                "sub_command": "list",
                "success": True,
            },
            "start_time": "2025-05-16T10:30:45.123Z",
            "end_time": "2025-05-16T10:30:46.123Z",
        }

        event = self.mapper.map_event(span_dict, is_start=False)

        self.assertIsNotNone(event)
        self.assertEqual(event["source"], "rovodev command completed")
        self.assertEqual(event["action"], "completed")
        self.assertEqual(event["action_subject"], "command")
        self.assertEqual(event["attributes"]["command"], "/sessions")
        self.assertEqual(event["attributes"]["sub_command"], "list")
        self.assertEqual(event["attributes"]["sessionId"], "test-session")

    def test_map_command_error_event(self):
        """Test mapping of command error events."""
        # Set current session
        CurrentSession.set_session_id("test-session")

        span_dict = {
            "name": "command executed",
            "attributes": {
                "command_name": "/sessions",
                "sub_command": "list",
                "success": False,
                "error": "Permission denied",
            },
            "start_time": "2025-05-16T10:30:45.123Z",
            "end_time": "2025-05-16T10:30:46.123Z",
        }

        event = self.mapper.map_event(span_dict, is_start=False)

        self.assertIsNotNone(event)
        self.assertEqual(event["source"], "rovodev command error")
        self.assertEqual(event["action"], "error")
        self.assertEqual(event["action_subject"], "command")
        self.assertEqual(event["attributes"]["command"], "/sessions")
        self.assertEqual(event["attributes"]["sub_command"], "list")
        self.assertEqual(event["attributes"]["sessionId"], "test-session")
