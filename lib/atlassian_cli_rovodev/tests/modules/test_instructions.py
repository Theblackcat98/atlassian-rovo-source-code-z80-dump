from unittest.mock import patch

import pytest

import rovodev.modules.instructions as instructions_mod

# Sample instruction data for testing
instruction_yaml = """
instructions:
  - name: test_instruction
    description: Test instruction description
    content_file: test_instruction.md
  - name: no_content_instruction
    description: No content instruction
    content_file: missing.md
"""


def write_yaml(tmp_path, content):
    file = tmp_path / "instructions.yml"
    file.write_text(content)
    return file


def write_content_file(tmp_path, filename, content):
    file = tmp_path / filename
    file.write_text(content)
    return file


@pytest.fixture
def patch_config_locations(tmp_path):
    # Patch get_config_locations to only return our temp file
    with patch.object(instructions_mod, "get_config_locations", return_value=[tmp_path / "instructions.yml"]):
        yield


def test_load_instruction_file(tmp_path):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    file = write_yaml(tmp_path, instruction_yaml)
    config = instructions_mod.load_instruction_file(file)
    assert config is not None
    assert len(config.instructions) == 1  # Only one should load (the other has missing content file)
    assert config.instructions[0].name == "test_instruction"
    assert config.instructions[0].content == "This is a test instruction content."


def test_load_instruction_config_merges_and_skips_duplicates(tmp_path, patch_config_locations):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    file = write_yaml(tmp_path, instruction_yaml)
    config = instructions_mod.load_instruction_config()
    assert config is not None
    names = [inst.name for inst in config.instructions]
    assert "test_instruction" in names
    # no_content_instruction should not be in the list because its content file is missing


def test_handle_instructions_command_with_input_success(tmp_path, patch_config_locations):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    write_yaml(tmp_path, instruction_yaml)
    result = instructions_mod.handle_instructions_command("test_instruction")
    assert result == "This is a test instruction content."


def test_handle_instructions_command_with_input_and_additional_text(tmp_path, patch_config_locations):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    write_yaml(tmp_path, instruction_yaml)
    result = instructions_mod.handle_instructions_command("test_instruction some additional text")
    expected = "This is a test instruction content.\n\nAdditional instructions: some additional text"
    assert result == expected


def test_handle_instructions_command_with_input_instruction_not_found(tmp_path, patch_config_locations):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    write_yaml(tmp_path, instruction_yaml)
    result = instructions_mod.handle_instructions_command("not_an_instruction")
    assert result is None


@patch("rovodev.modules.instructions.user_menu_panel_sync")
def test_handle_instructions_command_interactive(mock_user_menu_panel, tmp_path, patch_config_locations):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    write_yaml(tmp_path, instruction_yaml)
    # Simulate selecting the first instruction
    mock_instruction = instructions_mod.Instruction(
        name="test_instruction",
        description="Test instruction description",
        content_file="test_instruction.md",
        content="This is a test instruction content.",
    )
    mock_user_menu_panel.return_value = mock_instruction
    result = instructions_mod.handle_instructions_command()
    assert result == "This is a test instruction content."


@patch("rovodev.modules.instructions.user_menu_panel_sync")
def test_handle_instructions_command_interactive_cancelled(mock_user_menu_panel, tmp_path, patch_config_locations):
    # Create content files
    write_content_file(tmp_path, "test_instruction.md", "This is a test instruction content.")

    write_yaml(tmp_path, instruction_yaml)
    # Simulate user cancelling the selection
    mock_user_menu_panel.return_value = None
    result = instructions_mod.handle_instructions_command()
    assert result is None


def test_handle_instructions_command_no_instructions(tmp_path, patch_config_locations):
    # Write empty instructions file
    write_yaml(tmp_path, "instructions: []\n")
    result = instructions_mod.handle_instructions_command()
    assert result is None
