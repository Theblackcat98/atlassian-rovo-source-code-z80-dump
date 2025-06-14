"""Unit tests for the config command."""

import os
import subprocess
import sys
from unittest.mock import patch

import pytest

from rovodev.commands.config.command import config, detect_editor


@pytest.fixture
def clear_required_env_vars():
    """Fixture to remove all environment variables that affect editor detection."""
    required_vars = [
        "VSCODE_PROFILE_INITIALIZED",
        "__CFBundleIdentifier",
        "VSCODE_INJECTION",
        "CURSOR_TRACE_ID",
        "EDITOR",
    ]
    with patch.dict(os.environ, {var: "" for var in required_vars}, clear=True):
        yield


def test_detect_editor_vscode(clear_required_env_vars):
    """Test editor detection when running in VSCode."""
    with patch.dict(os.environ, {"VSCODE_PROFILE_INITIALIZED": "1"}):
        assert detect_editor() == "code"

    with patch.dict(os.environ, {"__CFBundleIdentifier": "com.microsoft.VSCode"}):
        assert detect_editor() == "code"

    with patch.dict(os.environ, {"VSCODE_INJECTION": "1"}):
        assert detect_editor() == "code"


def test_detect_editor_cursor(clear_required_env_vars):
    """Test editor detection when running in Cursor."""
    with patch.dict(os.environ, {"__CFBundleIdentifier": "com.todesktop.230313mzl4w4u92"}):
        assert detect_editor() == "cursor"

    with patch.dict(os.environ, {"CURSOR_TRACE_ID": "some-trace-id"}):
        assert detect_editor() == "cursor"


def test_detect_editor_jetbrains(clear_required_env_vars):
    """Test editor detection when running in JetBrains IDE."""
    with patch.dict(os.environ, {"__CFBundleIdentifier": "com.jetbrains.intellij"}):
        assert detect_editor() == "idea"


def test_detect_editor_none(clear_required_env_vars):
    """Test editor detection when no known editor is detected."""
    with patch.dict(os.environ, {}, clear=True):
        assert detect_editor() is None


@pytest.fixture
def mock_config_path(tmp_path):
    """Create a temporary config path for testing."""
    config_path = tmp_path / "config.yaml"
    with patch("rovodev.commands.config.command.DEFAULT_CONFIG_PATH", str(config_path)):
        yield config_path


def test_config_creates_file(mock_config_path, clear_required_env_vars):
    """Test that the config command creates the config file if it doesn't exist."""
    editor = "cat" if sys.platform != "win32" else "C:\\Windows\\system32\\notepad.exe"
    with patch.dict(os.environ, {"EDITOR": editor}):
        with patch("subprocess.run") as mock_run:
            config()
            assert mock_config_path.exists()
            mock_run.assert_called_once_with([editor, str(mock_config_path)], check=True)


def test_config_no_editor(mock_config_path, clear_required_env_vars):
    """Test config command behavior when no editor is detected."""
    with patch("rovodev.commands.config.command.detect_editor", return_value=None):
        with patch("rich.print") as mock_rich_print:
            config()
            mock_rich_print.assert_called_once()
            printed_message = mock_rich_print.call_args[0][0]
            assert "Could not detect editor" in printed_message
            assert str(mock_config_path) in printed_message


def test_config_editor_not_found(mock_config_path, clear_required_env_vars):
    """Test config command behavior when the editor command is not found."""
    with patch.dict(os.environ, {"EDITOR": "nonexistent"}):
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "nonexistent")):
            with patch("rich.print") as mock_rich_print:
                config()
                mock_rich_print.assert_called_once()
                printed_message = mock_rich_print.call_args[0][0]
                assert "Failed to open file" in printed_message
                assert str(mock_config_path) in printed_message
                assert "nonexistent" in printed_message


def test_config_editor_fails(mock_config_path, clear_required_env_vars):
    """Test config command behavior when the editor command fails."""
    editor = "cat" if sys.platform != "win32" else "C:\\Windows\\system32\\notepad.exe"
    with patch.dict(os.environ, {"EDITOR": editor}):
        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "cat")):
            with patch("rich.print") as mock_rich_print:
                config()
                mock_rich_print.assert_called_once()
                printed_message = mock_rich_print.call_args[0][0]
                assert "Failed to open file" in printed_message
                assert str(mock_config_path) in printed_message
                assert "cat" in printed_message
