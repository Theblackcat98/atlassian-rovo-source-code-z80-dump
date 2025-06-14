"""Tests for command registry analytics tracking."""

import unittest
from unittest.mock import MagicMock, patch

from rovodev.commands.run.command_registry import CommandRegistry


class TestCommandRegistryTracking(unittest.TestCase):
    """Tests for command registry analytics tracking."""

    def setUp(self):
        # Get the singleton instance
        self.registry = CommandRegistry()

        # Clear existing commands
        self.registry._commands.clear()

        # Register test commands
        def test_command(*args, **kwargs):
            return {"continue": True, "session_id": "test-session"}

        self.registry._commands["/test"] = {None: (test_command, "Test command")}

        def test_subcommand(*args, **kwargs):
            return {"other_data": "sensitive"}

        self.registry._commands["/test"]["sub"] = (test_subcommand, "Test subcommand")

    @patch("rovodev.modules.analytics.instrumentation.command.logfire.span")
    def test_command_tracking_success(self, mock_span):
        """Test that successful command execution is tracked."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Execute a command
        result = self.registry.dispatch("/test")

        # Verify span was created
        mock_span.assert_called_once_with("command executed")

        # Verify command attributes
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/test")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

        # Verify no result data was included
        for call in mock_span_ctx.set_attribute.call_args_list:
            args = call[0]
            self.assertNotIn("continue", args[0])
            self.assertNotIn("target_session_id", args[0])
            self.assertNotIn("result", args[0])

    @patch("rovodev.modules.analytics.instrumentation.command.logfire.span")
    def test_command_tracking_with_subcommand(self, mock_span):
        """Test that command with subcommand is tracked."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Execute a command with subcommand
        result = self.registry.dispatch("/test sub arg1 arg2")

        # Verify span was created
        mock_span.assert_called_once_with("command executed")

        # Verify command attributes
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/test")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "sub")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

        # Verify no result was added to span (only essential attributes)
        # Check that sensitive data was not included
        for call in mock_span_ctx.set_attribute.call_args_list:
            args = call[0]
            self.assertNotIn("result", args)  # Result should not be added as an attribute
            self.assertNotIn("other_data", str(args))  # Sensitive data should not be included

    @patch("rovodev.modules.analytics.instrumentation.command.logfire.span")
    def test_command_tracking_error(self, mock_span):
        """Test that command errors are tracked."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Register a command that raises an error
        @self.registry.register("/error", None, "Error command")
        def error_command(*args, **kwargs):
            raise ValueError("Test error")

        # Execute the command and expect an error
        with self.assertRaises(ValueError):
            self.registry.dispatch("/error")

        # Verify span was created
        mock_span.assert_called_once_with("command executed")

        # Verify error attributes
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/error")
        mock_span_ctx.set_attribute.assert_any_call("success", False)
        mock_span_ctx.set_attribute.assert_any_call("error", "Test error")

    @patch("rovodev.modules.analytics.instrumentation.command.logfire.span")
    def test_help_command_tracking(self, mock_span):
        """Test that help commands are tracked properly."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Test /help command
        self.registry.dispatch("/help")
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/help")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

        # Reset mocks
        mock_span.reset_mock()
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Test command help
        self.registry.dispatch("/test help")
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/test")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "help")
        mock_span_ctx.set_attribute.assert_any_call("success", True)
