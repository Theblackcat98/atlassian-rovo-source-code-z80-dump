import json
import shutil
from unittest.mock import patch

import pytest
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.usage import Usage

from rovodev.modules.sessions import Session, get_latest_usage, get_sessions, handle_sessions_command

mock_session_data = {
    "agent_factory": {},
    "message_history": [
        {
            "parts": [
                {
                    "content": "Explore this repo",
                    "timestamp": "2025-05-22T19:54:14.644574Z",
                    "part_kind": "user-prompt",
                },
            ],
            "kind": "request",
        }
    ],
    "usage": {},
    "run_step": 0,
    "model_settings": {"max_tokens": 4096, "temperature": 0.3},
    "mcp_servers": [],
    "run_state": {},
    "artifacts": {"metadata.json": {"title": "Repository Exploration Request", "fork_data": None}},
    "initial_prompt": "Explore this repo",
    "timestamp": 1747943654,
    "id": "fe1a4288-f3a4-4db9-a913-55d0ad0a5cc3",
}


def test_get_sessions(tmp_path):
    """Test the get_sessions function."""
    # Create some test sessions
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()

    # Create session 1
    session1_dir = session_dir / "session1"
    session1_dir.mkdir()
    (session1_dir / "session_context.json").write_text(json.dumps(mock_session_data, indent=4))

    # Create session 2 with a later timestamp
    session2_dir = session_dir / "session2"
    session2_dir.mkdir()
    mock_session_data["timestamp"] = mock_session_data["timestamp"] + 1000
    (session2_dir / "session_context.json").write_text(json.dumps(mock_session_data, indent=4))

    # Test getting sessions
    sessions = get_sessions(session_dir)
    assert len(sessions) == 2
    assert "session1" in sessions
    assert "session2" in sessions
    assert sessions["session1"].num_messages == 1
    assert sessions["session2"].num_messages == 1
    assert sessions["session1"].initial_prompt == "Explore this repo..."
    assert sessions["session2"].initial_prompt == "Explore this repo..."

    # Test empty directory
    shutil.rmtree(session_dir)
    session_dir.mkdir()
    sessions = get_sessions(session_dir)
    assert len(sessions) == 0


def test_get_latest_usage():
    """Test the get_latest_usage function."""
    # Test empty message history
    assert get_latest_usage([]) == Usage()

    # Test message history with no responses
    message_history = [ModelRequest(parts=[UserPromptPart(content="test")])]
    assert get_latest_usage(message_history) == Usage()  # type: ignore

    # Test message history with responses
    message_history = [
        ModelRequest(parts=[UserPromptPart(content="test")]),
        ModelResponse(
            parts=[TextPart(content="response")], usage=Usage(request_tokens=5, response_tokens=10, total_tokens=15)
        ),
        ModelRequest(parts=[UserPromptPart(content="test 2")]),
        ModelResponse(
            parts=[TextPart(content="response 2")], usage=Usage(request_tokens=15, response_tokens=25, total_tokens=40)
        ),
    ]
    latest_usage = get_latest_usage(message_history)
    assert latest_usage.request_tokens == 15
    assert latest_usage.response_tokens == 25
    assert latest_usage.total_tokens == 40


@pytest.mark.asyncio
async def test_handle_sessions_command(tmp_path):
    """Test the handle_sessions_command function."""
    # Create a test session
    session_dir = tmp_path / "sessions"
    session_dir.mkdir()
    session1_dir = session_dir / "session1"
    session1_dir.mkdir()
    session1_messages = [{"kind": "request", "parts": [{"part_kind": "user-prompt", "content": "test message 1"}]}]
    (session1_dir / "message_history.json").write_text(json.dumps(session1_messages))

    # Mock session_menu_panel to return a specific session and is_new_session flag
    mock_session = Session(session_id="session1", path=session1_dir)
    with patch("rovodev.modules.sessions.session_menu_panel") as mock_menu:
        # Test selecting an existing session
        mock_menu.return_value = (mock_session, False)
        selected_session, is_new = handle_sessions_command(session_dir, "session1")
        assert selected_session == mock_session
        assert not is_new
        mock_menu.assert_called_once()

        # Test creating a new session
        mock_menu.reset_mock()
        mock_menu.return_value = (mock_session, True)
        selected_session, is_new = handle_sessions_command(session_dir, "session1")
        assert selected_session == mock_session
        assert is_new
        mock_menu.assert_called_once()
