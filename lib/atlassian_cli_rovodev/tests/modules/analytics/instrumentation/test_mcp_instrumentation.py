"""Tests for MCP instrumentation."""

from unittest.mock import MagicMock, patch

import pytest

from nemo.utils.observability import (
    track_mcp_server_shutdown,
    track_mcp_server_startup,
)


class TestMCPInstrumentation:
    """Tests for MCP instrumentation."""

    @pytest.fixture
    def server_info(self):
        return {
            "stdio": ("stdio", "python -m scout.main run"),
            "http": ("http", "http://localhost:8000/mcp"),
        }

    @pytest.mark.asyncio
    @patch("logfire.span")
    async def test_track_server_startup(self, mock_span, server_info):
        """Test tracking successful server startup."""
        test_cases = [
            ("stdio server", *server_info["stdio"]),
            ("http server", *server_info["http"]),
        ]

        for case_name, server_type, connection_info in test_cases:
            # Set up mock span
            mock_span_ctx = MagicMock()
            mock_span.return_value.__enter__.return_value = mock_span_ctx

            # Use the context manager
            async with track_mcp_server_startup(server_type, connection_info) as span:
                # Simulate server operation
                span.set_attribute("custom_metric", 42)

            # Verify the span was created with the correct name
            mock_span.assert_called_with("mcp_server_startup")

            # Verify attributes were set correctly
            mock_span_ctx.set_attribute.assert_any_call("server_type", server_type)
            mock_span_ctx.set_attribute.assert_any_call("connection_info", connection_info)
            mock_span_ctx.set_attribute.assert_any_call("custom_metric", 42)
            mock_span_ctx.set_attribute.assert_any_call("success", True)

    @pytest.mark.asyncio
    @patch("logfire.span")
    async def test_track_server_shutdown(self, mock_span, server_info):
        """Test tracking successful server shutdown."""
        test_cases = [
            ("stdio server", *server_info["stdio"]),
            ("http server", *server_info["http"]),
        ]

        for case_name, server_type, connection_info in test_cases:
            # Set up mock span
            mock_span_ctx = MagicMock()
            mock_span.return_value.__enter__.return_value = mock_span_ctx

            # Use the context manager
            async with track_mcp_server_shutdown(server_type, connection_info) as span:
                # Simulate server operation
                span.set_attribute("custom_metric", 42)

            # Verify the span was created with the correct name
            mock_span.assert_called_with("mcp_server_shutdown")

            # Verify attributes were set correctly
            mock_span_ctx.set_attribute.assert_any_call("server_type", server_type)
            mock_span_ctx.set_attribute.assert_any_call("connection_info", connection_info)
            mock_span_ctx.set_attribute.assert_any_call("custom_metric", 42)
            mock_span_ctx.set_attribute.assert_any_call("success", True)

    @pytest.mark.asyncio
    @patch("logfire.span")
    async def test_track_server_errors(self, mock_span, server_info):
        """Test tracking server errors."""
        test_cases = [
            ("startup error", track_mcp_server_startup, "Failed to start server"),
            ("shutdown error", track_mcp_server_shutdown, "Failed to stop server"),
        ]

        for case_name, tracker, error_msg in test_cases:
            # Set up mock span
            mock_span_ctx = MagicMock()
            mock_span.return_value.__enter__.return_value = mock_span_ctx

            # Use the context manager with an error
            with pytest.raises(ValueError):
                async with tracker(*server_info["stdio"]):
                    raise ValueError(error_msg)

            # Verify attributes were set correctly
            mock_span_ctx.set_attribute.assert_any_call("server_type", server_info["stdio"][0])
            mock_span_ctx.set_attribute.assert_any_call("connection_info", server_info["stdio"][1])
            mock_span_ctx.set_attribute.assert_any_call("success", False)
            mock_span_ctx.set_attribute.assert_any_call("error", error_msg)
