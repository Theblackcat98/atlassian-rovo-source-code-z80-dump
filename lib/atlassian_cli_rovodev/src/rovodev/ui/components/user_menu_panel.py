import asyncio
from typing import Any, TypedDict

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import DummyOutput
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel

from nemo.constants import DEFAULT_PANEL_WIDTH

console = Console()

DEFAULT_MENU_FOOTER = "[bright_black]↑↓: Navigate | Enter ⏎: {action} | Esc: Cancel[/bright_black]"


class Choice(TypedDict):
    name: str
    value: Any


async def user_menu_panel(
    choices: list[Choice],
    message: str | None = None,
    selection: int | None = None,
    title: str | None = None,
    border_color: str = "dark_orange",
    title_color: str = "orange1",
    header: str | None = None,
    footer: str = DEFAULT_MENU_FOOTER,
    escape_return_value: Any = None,
    action_name: str = "Select",
) -> Any:
    """Display a menu with choices inside a panel and return the selected value.

    Args:
        message: The message to display above the choices.
        choices: A list of choices to display, each choice is a dictionary with 'name' and 'value' keys.
        selection: The index of the initially selected choice.
        title: The title of the panel.
        border_color: The color of the panel border.
        title_color: The color of the panel title.
        header: An optional header to display above the menu panel.
        footer: Footer text to display below the choices, defaults to a standard navigation hint.
        escape_return_value: An optional value to return when the user presses ESC.
        action_name: The name to use for the Enter key action in the footer.
    """
    buffer = Buffer()
    selection = selection or 0
    selection_info = {"index": selection, "choice": choices[selection]}
    kb = KeyBindings()

    footer = footer.format(action=action_name)

    @kb.add("c-c")
    def _(event: KeyPressEvent) -> None:
        """Ctrl-C to cancel"""
        event.app.exit(exception=KeyboardInterrupt())

    @kb.add("down")
    def _(event: KeyPressEvent) -> None:
        selection_info["index"] = (selection_info["index"] + 1) % len(choices)
        selection_info["choice"] = choices[selection_info["index"]]

    @kb.add("up")
    def _(event: KeyPressEvent) -> None:
        selection_info["index"] = (selection_info["index"] - 1) % len(choices)
        selection_info["choice"] = choices[selection_info["index"]]

    @kb.add("enter")
    def _(event: KeyPressEvent) -> None:
        """Enter to accept"""
        event.app.exit()

    @kb.add("escape")
    def _(event: KeyPressEvent) -> None:
        """Handle escape key"""
        selection_info["index"] = None
        event.app.exit()

    # Create dummy layout for prompt-toolkit
    layout = Layout(Window(BufferControl(buffer=buffer)))

    # Create application
    app = Application(
        output=DummyOutput(),
        layout=layout,
        key_bindings=kb,
        full_screen=False,
        erase_when_done=True,
        mouse_support=False,
        paste_mode=True,
    )

    def create_panel() -> Group:
        text = []
        if message:
            text = [message + "\n"]
        for i, choice in enumerate(choices):
            if i == selection_info["index"]:
                text.append(f"[blue bold]> {choice['name']}[/blue bold]")
            else:
                text.append(f"  {choice['name']}")
        panel_content = "\n" + "\n".join(text) + "\n"
        render_parts = []
        if header:
            render_parts.append(header)
        render_parts += [
            "",
            Panel(
                panel_content,
                width=DEFAULT_PANEL_WIDTH,
                border_style=border_color,
                title=f"[{title_color}]{title}[/{title_color}]" if title else None,
                title_align="left",
            ),
            footer if footer else "",
            "",
        ]
        return Group(*render_parts)

    if console._live is not None:
        console._live.stop()
        console._live = None
    with Live(create_panel(), console=console, auto_refresh=False, transient=True) as live:

        def before_render(_: Application) -> None:
            live.update(create_panel())
            live.refresh()

        app.before_render += before_render
        await app.run_async()

    if selection_info["index"] is None:
        # User pressed ESC or cancelled
        return escape_return_value

    return choices[selection_info["index"]]["value"]


def user_menu_panel_sync(
    choices: list[Choice],
    message: str | None = None,
    selection: int | None = None,
    title: str | None = None,
    border_color: str = "dark_orange",
    title_color: str = "orange1",
    header: str | None = None,
    footer: str = DEFAULT_MENU_FOOTER,
    escape_return_value: Any = None,
    action_name: str = "Select",
) -> Any:
    """Synchronous wrapper for user_menu_panel."""
    result = asyncio.run(
        asyncio.gather(  # type: ignore
            user_menu_panel(
                choices=choices,
                message=message,
                selection=selection,
                title=title,
                border_color=border_color,
                title_color=title_color,
                header=header,
                footer=footer,
                escape_return_value=escape_return_value,
                action_name=action_name,
            ),
            return_exceptions=True,
        )
    )
    # Check if the result contains an exception
    if result and len(result) > 0 and isinstance(result[0], Exception):
        raise result[0]
    return result[0]
