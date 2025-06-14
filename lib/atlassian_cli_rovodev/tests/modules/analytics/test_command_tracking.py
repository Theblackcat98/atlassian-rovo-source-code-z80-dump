"""Tests for command tracking analytics."""

import unittest
from unittest.mock import MagicMock, patch

import logfire

from rovodev.commands.run.command_registry import CommandRegistry
from rovodev.modules.analytics.instrumentation import command as command_instrumentation


class TestCommandTracking(unittest.TestCase):
    """Test command tracking behavior."""

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
        @self.registry.register("/memory", None, "Memory management")
        def memory_command(*args, **kwargs):
            return None

        @self.registry.register("/memory", "init", "Initialize memory")
        def memory_init_command(*args, **kwargs):
            return None

        # Register a command without subcommands (like #)
        @self.registry.register("#", None, "Add note")
        def note_command(*args, **kwargs):
            return None

    @patch.object(logfire, "span")
    def test_command_with_subcommands(self, mock_span):
        """Test tracking of commands that have subcommands."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # When using a valid subcommand
        self.registry.dispatch("/memory init some args")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/memory")
        mock_span_ctx.set_attribute.assert_any_call("sub_command", "init")
        mock_span_ctx.set_attribute.assert_any_call("success", True)

        # When using an invalid subcommand - should fall back to main command
        mock_span.reset_mock()
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        self.registry.dispatch("/memory invalid_subcommand some args")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "/memory")
        # Should not have sub_command attribute
        self.assertNotIn(
            ("sub_command", "invalid_subcommand"),
            [(call[0][0], call[0][1]) for call in mock_span_ctx.set_attribute.call_args_list],
        )
        mock_span_ctx.set_attribute.assert_any_call("success", True)

    @patch.object(logfire, "span")
    def test_command_without_subcommands(self, mock_span):
        """Test tracking of commands that don't have subcommands."""
        # Set up mock span
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        # Issue: This currently tracks "note text" as a subcommand when it should be an argument
        self.registry.dispatch("# note text")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "#")
        # Should not have sub_command attribute
        self.assertNotIn(
            ("sub_command", "note"), [(call[0][0], call[0][1]) for call in mock_span_ctx.set_attribute.call_args_list]
        )
        mock_span_ctx.set_attribute.assert_any_call("success", True)

        # Test with multiple arguments
        mock_span.reset_mock()
        mock_span_ctx = MagicMock()
        mock_span.return_value.__enter__.return_value = mock_span_ctx

        self.registry.dispatch("# first second third")

        # Verify span was created with correct attributes
        mock_span.assert_called_with("command executed")
        mock_span_ctx.set_attribute.assert_any_call("command_name", "#")
        # Should not have sub_command attribute
        self.assertNotIn(
            ("sub_command", "first"), [(call[0][0], call[0][1]) for call in mock_span_ctx.set_attribute.call_args_list]
        )
        mock_span_ctx.set_attribute.assert_any_call("success", True)
