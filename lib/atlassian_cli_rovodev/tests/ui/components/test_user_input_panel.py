"""Tests for the user_input_panel function."""

from unittest.mock import patch

import pytest
from prompt_toolkit import PromptSession
from prompt_toolkit.application import create_app_session
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from rovodev.ui.components.user_input_panel import user_input_panel


@pytest.fixture(autouse=True, scope="function")
def mock_input():
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input


@pytest.fixture
def prompt_session():
    """Create a prompt session with in-memory history."""
    return PromptSession(history=InMemoryHistory())


@pytest.mark.asyncio
async def test_basic_input(mock_input):
    """Test basic text input and submission."""
    with patch("rovodev.ui.components.user_input_panel.create_output", return_value=DummyOutput()):
        mock_input.send_text("Hello World\r")
        result = await user_input_panel()
        assert result == "Hello World"


@pytest.mark.asyncio
async def test_multiline_input_with_backslash(mock_input):
    """Test multiline input using backslash continuation."""
    with patch("rovodev.ui.components.user_input_panel.create_output", return_value=DummyOutput()):
        mock_input.send_text("Line 1\\\nLine 2\r")
        result = await user_input_panel()
        assert result == "Line 1\nLine 2"


@pytest.mark.asyncio
async def test_command_suggestion(mock_input):
    """Test that typing '/' shows command suggestions."""
    with patch("rovodev.ui.components.user_input_panel.create_output", return_value=DummyOutput()):
        mock_input.send_text("/\r")
        result = await user_input_panel()
        assert result == "/"


@pytest.mark.asyncio
async def test_history_support(mock_input, prompt_session):
    """Test that input is saved to history when prompt_session is provided."""
    with patch("rovodev.ui.components.user_input_panel.create_output", return_value=DummyOutput()):
        test_input = "Test input for history"
        mock_input.send_text(f"{test_input}\r")
        result = await user_input_panel(prompt_session)

        assert result == test_input
        assert test_input in prompt_session.history.get_strings()


@pytest.mark.asyncio
async def test_tab_key_indentation(mock_input):
    """Test that tab key adds indentation when no suggestion is present."""
    with patch("rovodev.ui.components.user_input_panel.create_output", return_value=DummyOutput()):
        mock_input.send_text("\t\r")  # Send tab then enter
        result = await user_input_panel()
        assert result == "    "  # 4 spaces for indentation
