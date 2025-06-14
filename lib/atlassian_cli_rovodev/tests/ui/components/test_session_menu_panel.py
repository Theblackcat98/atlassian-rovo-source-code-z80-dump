"""Tests for the session_menu_panel function."""

from pathlib import Path

import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput
from pydantic_ai.usage import Usage

from rovodev.modules.sessions import Session
from rovodev.ui.components.session_menu_panel import session_menu_panel


@pytest.fixture
def mock_session():
    """Create a mock session for testing."""
    return Session(
        session_id="test-session-id",
        title="Test Session",
        created="2023-01-01 12:00:00",
        last_saved="2023-01-02 12:00:00",
        num_messages=5,
        total_usage=Usage(request_tokens=100, response_tokens=200, total_tokens=300),
        latest_usage=Usage(request_tokens=50, response_tokens=100, total_tokens=150),
        context_limit=200000,
        initial_prompt="This is a test prompt...",
        path=Path("/fake/path/test-session-id"),
    )


@pytest.fixture
def mock_sessions(mock_session):
    """Create mock sessions dictionary for testing."""
    return {
        mock_session.session_id: mock_session,
        "second-session-id": Session(
            session_id="second-session-id",
            title="Second Session",
            created="2023-01-03 12:00:00",
            last_saved="2023-01-04 12:00:00",
            num_messages=3,
            total_usage=Usage(request_tokens=80, response_tokens=160, total_tokens=240),
            latest_usage=Usage(request_tokens=30, response_tokens=60, total_tokens=90),
            context_limit=200000,
            initial_prompt="Another test prompt...",
            path=Path("/fake/path/second-session-id"),
        ),
    }


@pytest.fixture(autouse=True, scope="function")
def mock_input():
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input


@pytest.mark.asyncio
async def test_session_menu_panel_basic(mock_sessions, mock_session, mock_input):
    """Test selecting the current session from the menu."""
    mock_input.send_text("\n")
    result, is_new = await session_menu_panel(mock_sessions, mock_session.session_id, Path("/fake/path"))

    assert result == mock_session
    assert not is_new


@pytest.mark.asyncio
async def test_session_menu_panel_navigation(mock_sessions, mock_session, mock_input):
    """Test selecting the next session from the menu."""
    mock_input.send_text("\x1b[B")  # Down key
    mock_input.send_text("\n")
    result, is_new = await session_menu_panel(mock_sessions, mock_session.session_id, Path("/fake/path"))

    assert result
    assert result != mock_session
    assert result.session_id == "second-session-id"
    assert not is_new

    # Test cycling back to the first session
    mock_input.send_text("\x1b[B")  # Down key
    mock_input.send_text("\x1b[B")  # Down key
    mock_input.send_text("\n")
    result, is_new = await session_menu_panel(mock_sessions, mock_session.session_id, Path("/fake/path"))

    assert result
    assert result == mock_session


@pytest.mark.asyncio
async def test_session_menu_panel_new_session(mock_sessions, mock_session, mock_input):
    """Test creating a new session from the menu."""
    mock_input.send_text("n")
    mock_input.send_text("\n")
    result, is_new = await session_menu_panel(mock_sessions, mock_session.session_id, Path("/fake/path"))

    assert result is None
    assert is_new


@pytest.mark.asyncio
async def test_session_menu_panel_delete_session(mock_sessions, mock_session, mock_input):
    """Test deleting sessions from the menu."""
    original_mock_sessions = mock_sessions.copy()
    # Test deleting the second session
    mock_input.send_text("\x1b[B")  # Down key
    mock_input.send_text("d")  # Delete
    mock_input.send_text("\n")  # Confirm
    mock_input.send_text("q")  # Quit
    assert len(mock_sessions) == 2
    result, is_new = await session_menu_panel(mock_sessions, mock_session.session_id, Path("/fake/path"))

    assert result is None
    assert not is_new
    assert len(mock_sessions) == 1

    # Test deleting then cancelling
    mock_input.send_text("d")  # Delete
    mock_input.send_text("\x1b[B")  # Down key to "No"
    mock_input.send_text("\n")  # Confirm
    mock_input.send_text("q")  # Quit
    result, is_new = await session_menu_panel(original_mock_sessions, mock_session.session_id, Path("/fake/path"))
    assert result is None
    assert not is_new
    assert len(original_mock_sessions) == 2


@pytest.mark.asyncio
async def test_session_menu_panel_cannot_delete_last_session(mock_session, mock_input):
    """Test that the last remaining session cannot be deleted."""
    # Create a sessions dict with only one session
    single_session_dict = {mock_session.session_id: mock_session}

    # Try to delete the only session, then select it when the menu reappears
    mock_input.send_text("d")  # Delete
    mock_input.send_text("\n")  # Select the session when menu reappears

    result, is_new = await session_menu_panel(single_session_dict, mock_session.session_id, Path("/fake/path"))

    # The session should still exist and be returned
    assert result == mock_session
    assert not is_new
    assert len(single_session_dict) == 1


@pytest.mark.asyncio
async def test_session_menu_panel_quit(mock_sessions, mock_session, mock_input):
    """Test quitting from the menu."""
    mock_input.send_text("\x1b[B")  # Down
    mock_input.send_text("\x1b[A")  # Up
    mock_input.send_text("\x1b[B")  # Down
    mock_input.send_text("q")  # Quit
    result, is_new = await session_menu_panel(mock_sessions, mock_session.session_id, Path("/fake/path"))

    assert result is None
    assert not is_new
