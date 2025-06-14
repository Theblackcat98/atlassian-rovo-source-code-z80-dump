"""Tests for MCP event mapper."""

import unittest
from unittest.mock import MagicMock

from rovodev.modules.analytics.instrumentation.session import CurrentSession
from rovodev.modules.analytics.mappers.mcp import MCPEventMapper


class TestMCPEventMapper(unittest.TestCase):
    def setUp(self):
        self.mapper = MCPEventMapper()
        CurrentSession.set_session_id("test-session")

        # Common test data
        self.base_span = {
            "start_time": "2025-05-16T10:30:45.123Z",
            "end_time": "2025-05-16T10:30:46.123Z",
        }
        self.stdio_attrs = {
            "server_type": "stdio",
            "connection_info": "python -m scout.main run",
        }
        self.http_attrs = {
            "server_type": "http",
            "connection_info": "http://localhost:8000/mcp",
        }

    def _assert_common_fields(self, event, expected_action: str, attributes: dict):
        """Assert common event fields."""
        self.assertEqual(event["action"], expected_action)
        self.assertEqual(event["action_subject"], "mcp_server")
        self.assertEqual(event["attributes"]["server_type"], attributes["server_type"])
        self.assertEqual(event["attributes"]["connection_info"], attributes["connection_info"])
        self.assertEqual(event["attributes"]["sessionId"], "test-session")
        # Verify AI feature attributes are correctly set
        self.assertEqual(event["attributes"]["isAIFeature"], 0)
        self.assertEqual(event["attributes"]["userGeneratedAI"], 0)
        self.assertNotIn("aiFeatureName", event["attributes"])

    def test_ignore_start_events(self):
        """Test that start events are ignored."""
        test_cases = [
            ("startup", {**self.base_span, "name": "mcp_server_startup"}),
            ("shutdown", {**self.base_span, "name": "mcp_server_shutdown"}),
        ]

        for case_name, span_dict in test_cases:
            with self.subTest(case=case_name):
                self.assertFalse(self.mapper.can_map(span_dict, is_start=True))
                self.assertIsNone(self.mapper.map_event(span_dict, is_start=True))

    def test_map_startup_events(self):
        """Test mapping of successful startup events for both server types."""
        test_cases = [
            ("stdio server", self.stdio_attrs),
            ("http server", self.http_attrs),
        ]

        for case_name, attrs in test_cases:
            with self.subTest(case=case_name):
                span_dict = {
                    **self.base_span,
                    "name": "mcp_server_startup",
                    "attributes": {**attrs, "success": True},
                }

                event = self.mapper.map_event(span_dict, is_start=False)

                self._assert_common_fields(event, "completed", attrs)
                self.assertEqual(event["source"], "rovodev mcp server startup")
                self.assertTrue(event["attributes"]["success"])

    def test_map_shutdown_events(self):
        """Test mapping of successful shutdown events for both server types."""
        test_cases = [
            ("stdio server", self.stdio_attrs),
            ("http server", self.http_attrs),
        ]

        for case_name, attrs in test_cases:
            with self.subTest(case=case_name):
                span_dict = {
                    **self.base_span,
                    "name": "mcp_server_shutdown",
                    "attributes": {**attrs, "success": True},
                }

                event = self.mapper.map_event(span_dict, is_start=False)

                self._assert_common_fields(event, "completed", attrs)
                self.assertEqual(event["source"], "rovodev mcp server shutdown")
                self.assertTrue(event["attributes"]["success"])

    def test_map_error_events(self):
        """Test mapping of error events."""
        test_cases = [
            (
                "startup error",
                "mcp_server_startup",
                "rovodev mcp server startup",
                "Failed to start server",
            ),
            (
                "shutdown error",
                "mcp_server_shutdown",
                "rovodev mcp server shutdown",
                "Failed to stop server",
            ),
        ]

        for case_name, span_name, expected_source, error_msg in test_cases:
            with self.subTest(case=case_name):
                span_dict = {
                    **self.base_span,
                    "name": span_name,
                    "attributes": {
                        **self.stdio_attrs,
                        "success": False,
                        "error": error_msg,
                    },
                }

                event = self.mapper.map_event(span_dict, is_start=False)

                self._assert_common_fields(event, "error", self.stdio_attrs)
                self.assertEqual(event["source"], expected_source)
                self.assertFalse(event["attributes"]["success"])
                self.assertEqual(event["attributes"]["error"], error_msg)
