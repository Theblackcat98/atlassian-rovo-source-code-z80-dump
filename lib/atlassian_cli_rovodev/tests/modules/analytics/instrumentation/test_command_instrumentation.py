"""Tests for command instrumentation."""

import unittest
from unittest.mock import MagicMock, patch

from rovodev.modules.analytics.instrumentation.command import track_command


class TestCommandInstrumentation(unittest.TestCase):
    """Tests for command instrumentation."""

    @patch("logfire.span")
    def test_track_command_success(self, mock_span):
        """Test tracking successful command execution."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Use the context manager
        with track_command(command="/sessions", sub_command="list") as span:
            # Simulate command execution
            span.set_attribute("some_metric", 42)

        # Verify the span was created with the correct name
        mock_span.assert_called_once_with("command executed")

        # Verify attributes were set correctly
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/sessions")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "list")
        mock_span_ctx.set_attribute.assert_any_call("some_metric", 42)
        mock_span_ctx.set_attribute.assert_any_call("success", True)

    @patch("logfire.span")
    def test_track_command_error(self, mock_span):
        """Test tracking command execution with error."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Use the context manager with an error
        with self.assertRaises(ValueError):
            with track_command(command="/sessions", sub_command="list"):
                raise ValueError("Something went wrong")

        # Verify the span was created with the correct name
        mock_span.assert_called_once_with("command executed")

        # Verify attributes were set correctly
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/sessions")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "list")
        mock_span_ctx.set_attribute.assert_any_call("success", False)
        mock_span_ctx.set_attribute.assert_any_call("error", "Something went wrong")

    @patch("logfire.span")
    def test_track_command_minimal(self, mock_span):
        """Test tracking command with minimal attributes."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Use the context manager with just the command
        with track_command(command="/help"):
            pass

        # Verify the span was created with the correct name
        mock_span.assert_called_once_with("command executed")

        # Verify only required attributes were set
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/help")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

        # Verify optional attributes were not set
        for call in mock_span_ctx.set_attribute.call_args_list:
            args = call[0]
            self.assertNotIn("sub_command", args)
            self.assertNotIn("command_args", args)
