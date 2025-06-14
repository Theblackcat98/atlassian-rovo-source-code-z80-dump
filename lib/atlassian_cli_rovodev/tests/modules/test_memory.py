"""Tests for the memory module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from rovodev.modules.memory import (
    get_memory_instructions,
    handle_memory_command,
    handle_memory_note,
    load_memories_from_file_system,
    sanitize_file_content,
)


def test_sanitize_file_content_should_remove_invisible_string():
    """Test sanitizing file content removes Unicode tag characters."""

    # This has invisible characters:
    #   " actually sus" - using language tags
    #   " sus with sneaky bits" - using sneaky bits
    #   " sus with variants" - using variant selectors
    # These will actually appear invisible in a code editor/bitbucket
    sanitized = "Definitely not sus"
    contaminated = "Definitely󠄐󠅣󠅥󠅣󠄐󠅧󠅙󠅤󠅘󠄐󠅦󠅑󠅢󠅙󠅑󠅞󠅤󠅣 not ⁢⁢⁤⁢⁢⁢⁢⁢⁢⁤⁤⁤⁢⁢⁤⁤⁢⁤⁤⁤⁢⁤⁢⁤⁢⁤⁤⁤⁢⁢⁤⁤⁢⁢⁤⁢⁢⁢⁢⁢⁢⁤⁤⁤⁢⁤⁤⁤⁢⁤⁤⁢⁤⁢⁢⁤⁢⁤⁤⁤⁢⁤⁢⁢⁢⁤⁤⁢⁤⁢⁢⁢⁢⁢⁤⁢⁢⁢⁢⁢⁢⁤⁤⁤⁢⁢⁤⁤⁢⁤⁤⁢⁤⁤⁤⁢⁢⁤⁤⁢⁢⁤⁢⁤⁢⁤⁤⁢⁢⁢⁢⁤⁢⁤⁤⁢⁤⁢⁤⁤⁢⁤⁤⁤⁤⁢⁢⁤⁢⁢⁤⁢⁢⁢⁢⁢⁢⁤⁤⁢⁢⁢⁤⁢⁢⁤⁤⁢⁤⁢⁢⁤⁢⁤⁤⁤⁢⁤⁢⁢⁢⁤⁤⁤⁢⁢⁤⁤sus󠀁󠀠󠁡󠁣󠁴󠁵󠁡󠁬󠁬󠁹󠀠󠁳󠁵󠁳󠁿"

    # Check that we definitely have invisible characters
    assert len(contaminated) > len(sanitized)
    assert sanitize_file_content(contaminated) == sanitized


def test_sanitize_file_content_should_remove_unicode_tags():
    content = "Normal\U000e0001\U000e0042\U000e0063text"
    assert sanitize_file_content(content) == "Normaltext"


def test_sanitize_file_content_should_remove_variation_selectors():
    content = "Normal\U000e0100\U000e0142\U000e01eftext"
    assert sanitize_file_content(content) == "Normaltext"


def test_sanitize_file_content_should_remove_invisible_operators():
    content = "Normal\u2062\u2063\u2064\u2065text"
    assert sanitize_file_content(content) == "Normaltext"


def test_sanitize_file_content_should_not_remove_characters_outside_of_range():
    # Test with characters outside the range (should not be removed)
    content = "Text \U000e0000\U000e0080 with out-of-range chars"  # Just outside range on both ends
    assert sanitize_file_content(content) == content


def test_sanitize_file_content_should_retain_formatting_and_punctuation():
    # Make sure we don't accidentally mangle valid inputs
    # The following does not contain any invisible strings of characters
    content = """
    ## This is some markdown
    It has new lines.
        And indents.
    
    This is a list
    - Point 1
        - Something indented
    - Point 2

    Wow! Such markdown.

    ```
    // Look at this code
    something = doesathing()
    ```
    """

    assert sanitize_file_content(content) == content


@pytest.fixture
def mock_file_system(tmp_path):
    """Create a mock file system with memory files."""
    # Create workspace memory files
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    (workspace_dir / ".agent.md").write_text("Workspace memory")

    # Create subdirectory with memory file
    subdir = workspace_dir / "subdir"
    subdir.mkdir()
    (subdir / ".agent.md").write_text("Subdir memory")

    return workspace_dir


@patch("pathlib.Path.home")
def test_load_memories_from_workspace(mock_home, mock_file_system, tmp_path):
    """Test loading memories from workspace directories."""
    mock_home.return_value = tmp_path
    memory, paths = load_memories_from_file_system(mock_file_system / "subdir")
    assert memory is not None
    assert "Instructions for the current directory" in memory
    assert "Instructions for ancestor directory" in memory
    # We expect 2 paths: current .agent.md, and ../.agent.md
    assert len(paths) == 2


@patch("pathlib.Path.home")
def test_load_memories_from_home(mock_home, tmp_path):
    """Test loading memories from user's home directory."""
    mock_home.return_value = tmp_path
    rovodev_dir = tmp_path / ".rovodev"
    rovodev_dir.mkdir(parents=True)
    (rovodev_dir / ".agent.md").write_text("User memory")

    memory, _ = load_memories_from_file_system(tmp_path)
    assert memory is not None
    assert "User memory" in memory


@patch("pathlib.Path.cwd")
def test_handle_memory_note_add(mock_cwd, tmp_path):
    """Test adding a memory note."""
    mock_cwd.return_value = tmp_path
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_text") as mock_read,
        patch("pathlib.Path.write_text") as mock_write,
    ):

        mock_exists.return_value = True
        mock_read.return_value = "# Existing content"

        handle_memory_note("New note")

        mock_write.assert_called_once()
        write_content = mock_write.call_args[0][0]
        assert "New note" in write_content
        assert "# Workspace notes" in write_content


@patch("pathlib.Path.cwd")
def test_handle_memory_note_remove(mock_cwd, tmp_path):
    """Test removing a memory note."""
    mock_cwd.return_value = tmp_path
    with (
        patch("pathlib.Path.exists") as mock_exists,
        patch("pathlib.Path.read_text") as mock_read,
        patch("pathlib.Path.write_text") as mock_write,
    ):

        mock_exists.return_value = True
        mock_read.return_value = "# Workspace notes\n- Note to remove\n- Keep this note"

        handle_memory_note("!Note to remove")

        mock_write.assert_called_once()
        write_content = mock_write.call_args[0][0]
        assert "Note to remove" not in write_content
        assert "Keep this note" in write_content


@patch.dict("os.environ", {"EDITOR": "test-editor"})
@patch("rovodev.commands.config.command.shutil.which")
@patch("pathlib.Path.cwd")
def test_handle_memory_command_default(mock_cwd, mock_which, tmp_path):
    """Test handling memory command with no arguments."""
    mock_cwd.return_value = tmp_path
    mock_which.return_value = "/usr/bin/test-editor"
    with patch("rovodev.commands.config.command.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = handle_memory_command(None)
        mock_run.assert_called_once()
        assert ".agent.md" in mock_run.call_args[0][0][1]
        assert result is None


@patch.dict("os.environ", {"EDITOR": "test-editor"})
@patch("rovodev.commands.config.command.shutil.which")
@patch("pathlib.Path.home")
def test_handle_memory_command_user(mock_home, mock_which, tmp_path):
    """Test handling memory command for user memory."""
    mock_home.return_value = tmp_path
    mock_which.return_value = "/usr/bin/test-editor"
    with patch("rovodev.commands.config.command.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        result = handle_memory_command("user")
        mock_run.assert_called_once()
        assert ".rovodev/.agent.md" in Path(mock_run.call_args[0][0][1]).as_posix()
        assert result is None


def test_handle_memory_command_init():
    """Test handling memory command for init."""
    result = handle_memory_command("init")
    assert "Your goal is to explore" in result  # type: ignore


@patch("pathlib.Path.cwd")
def test_get_memory_instructions_with_logging(mock_cwd, tmp_path):
    """Test getting memory instructions with path logging."""
    mock_cwd.return_value = tmp_path
    with (
        patch("rovodev.modules.memory.load_memories_from_file_system") as mock_load,
        patch("rich.console.Console.print") as mock_print,
    ):

        mock_load.return_value = ("Test memory", ["path1", "path2"])
        result = get_memory_instructions(log_paths=True)

        assert "Test memory" in result
        mock_print.assert_called_once()
        assert "path1" in mock_print.call_args[0][0]
        assert "path2" in mock_print.call_args[0][0]
