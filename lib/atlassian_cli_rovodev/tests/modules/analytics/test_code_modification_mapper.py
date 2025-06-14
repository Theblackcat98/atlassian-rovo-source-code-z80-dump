"""Tests for code modification mapper."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rovodev.modules.analytics.mappers.code_modification import CodeModificationMapper


class MockSpan:
    """Mock span for testing."""

    def __init__(self, span_dict):
        self.attributes = {}
        self.span_dict = span_dict

    def set_attribute(self, key, value):
        """Mock set_attribute method."""
        self.attributes[key] = value
        # Also update span_dict to simulate OTel behavior
        self.span_dict["attributes"][key] = value


@pytest.fixture
def mapper():
    """Create a code modification mapper."""
    return CodeModificationMapper()


def test_can_map_tools(mapper):
    """Test that mapper correctly identifies supported tools."""
    # Should map supported tools
    for tool in ["find_and_replace_code", "create_file", "delete_file"]:
        span = {"attributes": {"gen_ai.tool.name": tool}}
        assert mapper.can_map(span, True), f"Should map {tool}"
        assert mapper.can_map(span, False), f"Should map {tool}"

    # Should not map other tools
    span = {"attributes": {"gen_ai.tool.name": "other_tool"}}
    assert not mapper.can_map(span, True)
    assert not mapper.can_map(span, False)


def test_map_start_event(mapper):
    """Test mapping of start events."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "find_and_replace_code",
            "tool_arguments": json.dumps({"file_path": "test.py", "find": "old", "replace": "new"}),
        }
    }

    mock_span = MockSpan(span)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="original content"),
    ):
        event = mapper.map_event(span, is_start=True, span=mock_span)

    # Should store content in attributes but not send event
    assert event is None
    assert span["attributes"]["original_content"] == "original content"


def test_map_completion_event(mapper):
    """Test mapping of completion events."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "find_and_replace_code",
            "tool_arguments": json.dumps({"file_path": "test.py"}),
        },
        "attributes": {
            "gen_ai.tool.name": "find_and_replace_code",
            "tool_arguments": json.dumps({"file_path": "test.py"}),
            "original_content": "old content\nto modify\n",
        },
    }

    mock_span = MockSpan(span)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="new content\nmodified\n"),
    ):
        event = mapper.map_event(span, is_start=False, span=mock_span)

    assert event["source"] == "rovodev code completed"
    assert event["action"] == "completed"
    assert event["action_subject"] == "code_modification"
    assert event["attributes"]["tool_name"] == "find_and_replace_code"
    assert event["attributes"]["file_type"] == "py"
    assert event["attributes"]["lines_added"] == 2
    assert event["attributes"]["lines_removed"] == 2


def test_completion_without_original_content(mapper):
    """Test completion when original content wasn't stored."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "find_and_replace_code",
            "tool_arguments": json.dumps({"file_path": "test.py"}),
        }
    }

    mock_span = MockSpan(span)
    event = mapper.map_event(span, is_start=False, span=mock_span)
    assert event is None


def test_invalid_tool_arguments(mapper):
    """Test handling of invalid tool arguments."""
    span = {"attributes": {"gen_ai.tool.name": "find_and_replace_code", "tool_arguments": "invalid json"}}

    # Should handle error gracefully
    mock_span = MockSpan(span)
    event = mapper.map_event(span, is_start=True, span=mock_span)
    assert event is None

    event = mapper.map_event(span, is_start=False, span=mock_span)
    assert event is None


def test_file_not_found(mapper):
    """Test when file doesn't exist."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "find_and_replace_code",
            "tool_arguments": json.dumps({"file_path": "test.py"}),
        }
    }

    with patch("pathlib.Path.exists", return_value=False):
        # Should handle gracefully
        mock_span = MockSpan(span)
        event = mapper.map_event(span, is_start=True, span=mock_span)
        assert event is None

        event = mapper.map_event(span, is_start=False, span=mock_span)
        assert event is None


def test_create_file_start(mapper):
    """Test create_file start event."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "create_file",
            "tool_arguments": json.dumps({"file_path": "test.py", "initial_content": "def test():\n    pass\n"}),
        }
    }

    mock_span = MockSpan(span)
    event = mapper.map_event(span, is_start=True, span=mock_span)

    # Should store empty string as original content but not send event
    assert event is None
    assert mock_span.attributes["original_content"] == ""


def test_create_file_completion(mapper):
    """Test create_file completion event."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "create_file",
            "tool_arguments": json.dumps({"file_path": "test.py"}),
            "original_content": "",  # Empty for create
        }
    }

    mock_span = MockSpan(span)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="def test():\n    pass\n"),
    ):
        event = mapper.map_event(span, is_start=False, span=mock_span)

    assert event["source"] == "rovodev code completed"
    assert event["action"] == "completed"
    assert event["action_subject"] == "code_modification"
    assert event["attributes"]["tool_name"] == "create_file"
    assert event["attributes"]["file_type"] == "py"
    assert event["attributes"]["lines_added"] == 2
    assert event["attributes"]["lines_removed"] == 0


def test_delete_file_start(mapper):
    """Test delete_file start event."""
    span = {"attributes": {"gen_ai.tool.name": "delete_file", "tool_arguments": json.dumps({"file_path": "test.py"})}}

    mock_span = MockSpan(span)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="def test():\n    pass\n"),
    ):
        event = mapper.map_event(span, is_start=True, span=mock_span)

    # Should store original content but not send event
    assert event is None
    assert mock_span.attributes["original_content"] == "def test():\n    pass\n"


def test_delete_file_completion(mapper):
    """Test delete_file completion event."""
    original_content = "def test():\n    pass\n"
    span = {
        "attributes": {
            "gen_ai.tool.name": "delete_file",
            "tool_arguments": json.dumps({"file_path": "test.py"}),
            "original_content": original_content,
        }
    }

    mock_span = MockSpan(span)
    event = mapper.map_event(span, is_start=False, span=mock_span)

    assert event["source"] == "rovodev code completed"
    assert event["action"] == "completed"
    assert event["action_subject"] == "code_modification"
    assert event["attributes"]["tool_name"] == "delete_file"
    assert event["attributes"]["file_type"] == "py"
    assert event["attributes"]["language"] == "python"
    assert event["attributes"]["lines_added"] == 0
    assert event["attributes"]["lines_removed"] == 2


def test_file_without_extension(mapper):
    """Test handling of files without extension."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "create_file",
            "tool_arguments": json.dumps({"file_path": "Dockerfile"}),
            "original_content": "",
        }
    }

    mock_span = MockSpan(span)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="FROM python:3.10\nWORKDIR /app\n"),
    ):
        event = mapper.map_event(span, is_start=False, span=mock_span)

    assert event["source"] == "rovodev code completed"
    assert event["action"] == "completed"
    assert event["action_subject"] == "code_modification"
    assert event["attributes"]["tool_name"] == "create_file"
    assert event["attributes"]["file_type"] == "dockerfile"  # Special case handling
    assert event["attributes"]["language"] == "dockerfile"
    assert event["attributes"]["lines_added"] == 2
    assert event["attributes"]["lines_removed"] == 0


def test_unknown_file_type(mapper):
    """Test handling of files with unknown type."""
    span = {
        "attributes": {
            "gen_ai.tool.name": "create_file",
            "tool_arguments": json.dumps({"file_path": "some_file"}),
            "original_content": "",
        }
    }

    mock_span = MockSpan(span)
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.read_text", return_value="some content\n"),
    ):
        event = mapper.map_event(span, is_start=False, span=mock_span)

    assert event["source"] == "rovodev code completed"
    assert event["action"] == "completed"
    assert event["action_subject"] == "code_modification"
    assert event["attributes"]["tool_name"] == "create_file"
    assert event["attributes"]["file_type"] == "no_extension"
    assert event["attributes"]["language"] == "unknown"  # Default for unknown types
    assert event["attributes"]["lines_added"] == 1
    assert event["attributes"]["lines_removed"] == 0
