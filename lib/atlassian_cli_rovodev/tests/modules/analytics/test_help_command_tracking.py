"""Tests for help command tracking analytics."""

import unittest
from unittest.mock import MagicMock, patch

import logfire

from rovodev.commands.run.command_registry import CommandRegistry


class TestHelpCommandTracking(unittest.TestCase):
    """Test help command tracking behavior."""

    @classmethod
    def setUpClass(cls):
        # Configure logfire for testing
        logfire.configure(
            service_name="test",
            service_version="1.0.0",
            environment="test",
            send_to_logfire=False,
            console=False,
        )

    def setUp(self):
        # Get the singleton instance
        self.registry = CommandRegistry()
        # Clear existing commands
        self.registry._commands.clear()

        # Register test commands
        @self.registry.register("/test", None, "Test command")
        def test_command(*args, **kwargs):
            return None

        @self.registry.register("/test", "sub", "Test subcommand")
        def test_sub_command(*args, **kwargs):
            return None

    @patch.object(logfire, "span")
    def test_help_command_tracking(self, mock_span):
        """Test tracking of /help command."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Test /help command
        self.registry.dispatch("/help")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/help")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

    @patch.object(logfire, "span")
    def test_command_help_tracking(self, mock_span):
        """Test tracking of command help (e.g., /test help)."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Test command help
        self.registry.dispatch("/test help")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/test")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "help")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

    @patch.object(logfire, "span")
    def test_subcommand_help_tracking(self, mock_span):
        """Test tracking of subcommand help (e.g., /test sub help)."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Test subcommand help
        self.registry.dispatch("/test sub help")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/test")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "sub")
        mock_span_ctx.set_attribute.assert_any_call("success", True)
