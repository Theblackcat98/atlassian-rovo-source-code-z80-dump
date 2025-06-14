import pytest
from prompt_toolkit.application import create_app_session
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput

from rovodev.ui.components.user_menu_panel import Choice, user_menu_panel


@pytest.fixture(autouse=True, scope="function")
def mock_input():
    with create_pipe_input() as pipe_input:
        with create_app_session(input=pipe_input, output=DummyOutput()):
            yield pipe_input


@pytest.mark.asyncio
async def test_default_escape_behavior(mock_input):
    """Test that hitting the escape key exits the user menu and returns None."""
    mock_input.send_text("\x1b")  # Escape key
    result = await user_menu_panel(
        choices=[Choice(name="Choice 1", value="value1"), Choice(name="Choice 2", value="value2")]
    )
    assert result is None, "Expected None when escaping the user menu"


@pytest.mark.asyncio
async def test_custom_escape_behavior(mock_input):
    """Test that hitting the escape key returns the custom escape value."""
    mock_input.send_text("\x1b")  # Escape key
    result = await user_menu_panel(
        choices=[Choice(name="Choice 1", value="value1"), Choice(name="Choice 2", value="value2")],
        escape_return_value="custom_escape",
    )
    assert result == "custom_escape", "Expected custom escape value when escaping the user menu"


@pytest.mark.asyncio
async def test_default_selection_enter(mock_input):
    """Test that pressing enter selects the first/default option."""
    mock_input.send_text("\r")  # Enter key
    result = await user_menu_panel(
        choices=[Choice(name="Choice 1", value="value1"), Choice(name="Choice 2", value="value2")]
    )
    assert result == "value1", "Expected first choice to be selected when pressing enter"


@pytest.mark.asyncio
async def test_down_then_enter(mock_input):
    """Test pressing down arrow then enter selects the second option."""
    mock_input.send_text("\x1b[B\r")  # Down arrow then enter
    result = await user_menu_panel(
        choices=[Choice(name="Choice 1", value="value1"), Choice(name="Choice 2", value="value2")]
    )
    assert result == "value2", "Expected second choice to be selected after pressing down then enter"


@pytest.mark.asyncio
async def test_selection_wrapping(mock_input):
    """Test that selection wraps around to the start after reaching the end."""
    # Press down arrow two times (should wrap to first option) then enter
    mock_input.send_text("\x1b[B\x1b[B\r")
    result = await user_menu_panel(
        choices=[Choice(name="Choice 1", value="value1"), Choice(name="Choice 2", value="value2")]
    )
    assert result == "value1", "Expected selection to wrap around to first choice"
