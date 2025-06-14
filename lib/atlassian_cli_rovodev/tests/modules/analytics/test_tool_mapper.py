"""Tests for tool event mapper."""

from datetime import datetime, timedelta

import pytest

from rovodev.modules.analytics.instrumentation.session import CurrentSession
from rovodev.modules.analytics.mappers.base import DEFAULT_SESSION_ID
from rovodev.modules.analytics.mappers.tool import ToolEventMapper


@pytest.fixture
def tool_event_mapper():
    """Create a tool event mapper instance."""
    # Reset current session before each test
    CurrentSession.set_session_id(None)
    return ToolEventMapper()


def test_map_tool_start_event(tool_event_mapper):
    """Test mapping a tool start event."""
    # Set current session
    CurrentSession.set_session_id("test-session")

    # Create a mock span dictionary
    span_dict = {
        "name": "running tool",
        "attributes": {
            "gen_ai.tool.name": "open_files",
            "gen_ai.tool.call.id": "tool123",
        },
        "start_time": "2025-05-16T10:30:45.123Z",
    }

    # Map the event
    event = tool_event_mapper.map_event(span_dict, is_start=True)

    # Verify the mapped event
    assert event["source"] == "rovodev tool started"
    assert event["action"] == "started"
    assert event["action_subject"] == "llm_tool_call"
    assert event["attributes"]["tool_name"] == "open_files"
    assert event["attributes"]["tool_call_id"] == "tool123"


def test_map_tool_complete_event(tool_event_mapper):
    """Test mapping a tool complete event."""
    # Set current session
    CurrentSession.set_session_id("test-session")

    # Create a mock span dictionary
    now = datetime.now()
    one_second_later = now + timedelta(seconds=1)

    # Format as ISO strings
    start_time = now.isoformat()
    end_time = one_second_later.isoformat()

    span_dict = {
        "name": "running tool",
        "attributes": {
            "gen_ai.tool.name": "open_files",
            "gen_ai.tool.call.id": "tool123",
        },
        "start_time": start_time,
        "end_time": end_time,
    }

    # Map the event
    event = tool_event_mapper.map_event(span_dict, is_start=False)

    # Verify the mapped event
    assert event["source"] == "rovodev tool completed"
    assert event["action"] == "completed"
    assert event["action_subject"] == "llm_tool_call"
    assert event["attributes"]["tool_name"] == "open_files"
    assert event["attributes"]["tool_call_id"] == "tool123"
    assert "duration_ms" in event["attributes"]


def test_map_tool_error_event(tool_event_mapper):
    """Test mapping a tool error event."""
    # Set current session
    CurrentSession.set_session_id("test-session")

    # Create a mock span dictionary
    span_dict = {
        "name": "running tool",
        "attributes": {
            "gen_ai.tool.name": "open_files",
            "gen_ai.tool.call.id": "tool123",
            "error.type": "FileNotFoundError",
            "error.message": "File not found: file1.py",
        },
        "start_time": "2025-05-16T10:30:45.123Z",
        "end_time": "2025-05-16T10:30:46.123Z",
        "status": {"status_code": "ERROR"},
    }

    # Map the event
    event = tool_event_mapper.map_event(span_dict, is_start=False)

    # Verify the mapped event
    assert event["source"] == "rovodev tool error"
    assert event["action"] == "error"
    assert event["action_subject"] == "llm_tool_call"
    assert event["attributes"]["tool_name"] == "open_files"
    assert event["attributes"]["tool_call_id"] == "tool123"
    assert event["attributes"]["error_type"] == "FileNotFoundError"
    assert event["attributes"]["error_message"] == "File not found: file1.py"
    assert event["attributes"]["success"] is False


def test_missing_session_id(tool_event_mapper):
    """Test handling missing session ID."""
    # Reset current session before test
    CurrentSession.set_session_id(None)

    span_dict = {
        "name": "running tool",
        "attributes": {
            "gen_ai.tool.name": "open_files",
            "gen_ai.tool.call.id": "tool123",
        },
        "start_time": "2025-05-16T10:30:45.123Z",
    }

    # Map the event
    event = tool_event_mapper.map_event(span_dict, True)

    # Verify the mapped event has the default session ID
    assert event["attributes"]["sessionId"] == DEFAULT_SESSION_ID
