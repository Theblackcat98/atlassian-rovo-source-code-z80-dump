"""Tests for LLM error event mapping."""

import unittest
from unittest.mock import MagicMock

from rovodev.modules.analytics.instrumentation.session import CurrentSession
from rovodev.modules.analytics.mappers.llm import LLMEventMapper


class TestLLMErrorEventMapper(unittest.TestCase):
    """Test LLM error event mapping functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mapper = LLMEventMapper()
        # Set up a test session
        CurrentSession.set_session_id("test-session-123")

    def tearDown(self):
        """Clean up after tests."""
        CurrentSession.set_session_id(None)

    def test_normal_llm_span_mapping(self):
        """Test that normal LLM spans are mapped correctly."""
        span_dict = {
            "name": "chat",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4",
                "gen_ai.usage.input_tokens": 100,
                "gen_ai.usage.output_tokens": 50,
            },
            "status": {"status_code": "OK"},
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # Test that it can map
        self.assertTrue(self.mapper.can_map(span_dict, False))

        # Test mapping
        event = self.mapper.map_event(span_dict, False)
        self.assertIsNotNone(event)
        self.assertEqual(event["action"], "completed")
        self.assertEqual(event["source"], "rovodev llm completed")
        self.assertEqual(event["attributes"]["model_id"], "gpt-4")
        self.assertTrue(event["attributes"]["success"])

    def test_error_llm_span_mapping(self):
        """Test that error LLM spans are mapped to error events."""
        span_dict = {
            "name": "chat",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "gpt-4",
                "error.type": "RateLimitError",
                "error.message": "Rate limit exceeded",
            },
            "status": {"status_code": "ERROR", "description": "Rate limit exceeded"},
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        # Test that it can map
        self.assertTrue(self.mapper.can_map(span_dict, False))

        # Test mapping
        event = self.mapper.map_event(span_dict, False)
        self.assertIsNotNone(event)
        self.assertEqual(event["action"], "error")
        self.assertEqual(event["source"], "rovodev llm error")
        self.assertEqual(event["attributes"]["model_id"], "gpt-4")
        self.assertEqual(event["attributes"]["error_type"], "RateLimitError")
        self.assertEqual(event["attributes"]["error_message"], "Rate limit exceeded")

    def test_error_detection_with_different_error_types(self):
        """Test error detection with various error types."""
        error_cases = [
            {
                "error_type": "AuthenticationError",
                "error_message": "Invalid API key",
                "model": "claude-3",
            },
            {
                "error_type": "TimeoutError",
                "error_message": "Request timed out",
                "model": "gpt-3.5-turbo",
            },
            {
                "error_type": "ValidationError",
                "error_message": "Invalid input format",
                "model": "gemini-pro",
            },
        ]

        for case in error_cases:
            with self.subTest(error_type=case["error_type"]):
                span_dict = {
                    "name": "chat",
                    "attributes": {
                        "gen_ai.operation.name": "chat",
                        "gen_ai.request.model": case["model"],
                        "error.type": case["error_type"],
                        "error.message": case["error_message"],
                    },
                    "status": {"status_code": "ERROR", "description": case["error_message"]},
                    "start_time": 1000000000,
                    "end_time": 1000001000,
                }

                event = self.mapper.map_event(span_dict, False)
                self.assertIsNotNone(event)
                self.assertEqual(event["action"], "error")
                self.assertEqual(event["attributes"]["error_type"], case["error_type"])
                self.assertEqual(event["attributes"]["error_message"], case["error_message"])
                self.assertEqual(event["attributes"]["model_id"], case["model"])

    def test_error_vs_normal_status_detection(self):
        """Test that error status is correctly distinguished from normal status."""
        # Normal status codes that should NOT trigger error events
        normal_statuses = ["OK", "UNSET"]

        for status in normal_statuses:
            with self.subTest(status=status):
                span_dict = {
                    "name": "chat",
                    "attributes": {"gen_ai.operation.name": "chat"},
                    "status": {"status_code": status},
                    "start_time": 1000000000,
                    "end_time": 1000001000,
                }

                event = self.mapper.map_event(span_dict, False)
                self.assertIsNotNone(event)
                self.assertNotEqual(event["action"], "error")

        # Error status should trigger error event
        error_span_dict = {
            "name": "chat",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "error.type": "TestError",
                "error.message": "Test error message",
            },
            "status": {"status_code": "ERROR"},
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        event = self.mapper.map_event(error_span_dict, False)
        self.assertIsNotNone(event)
        self.assertEqual(event["action"], "error")

    def test_error_event_attributes(self):
        """Test that error events contain all required attributes."""
        span_dict = {
            "name": "chat",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "test-model",
                "error.type": "TestError",
                "error.message": "Test error message",
            },
            "status": {"status_code": "ERROR"},
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        event = self.mapper.map_event(span_dict, False)

        # Check required error attributes
        required_attrs = ["model_id", "error_type", "error_message", "timestamp", "sessionId"]
        for attr in required_attrs:
            self.assertIn(attr, event["attributes"], f"Missing required attribute: {attr}")

        # Check specific values
        self.assertEqual(event["attributes"]["model_id"], "test-model")
        self.assertEqual(event["attributes"]["error_type"], "TestError")
        self.assertEqual(event["attributes"]["error_message"], "Test error message")
        self.assertEqual(event["attributes"]["sessionId"], "test-session-123")

    def test_error_event_with_missing_error_attributes(self):
        """Test error event handling when error attributes are missing."""
        span_dict = {
            "name": "chat",
            "attributes": {
                "gen_ai.operation.name": "chat",
                "gen_ai.request.model": "test-model",
                # Missing error.type and error.message
            },
            "status": {"status_code": "ERROR"},
            "start_time": 1000000000,
            "end_time": 1000001000,
        }

        event = self.mapper.map_event(span_dict, False)

        # Should still create error event with defaults
        self.assertEqual(event["action"], "error")
        self.assertEqual(event["attributes"]["error_type"], "unknown")
        self.assertEqual(event["attributes"]["error_message"], "Unknown error")


if __name__ == "__main__":
    unittest.main()
