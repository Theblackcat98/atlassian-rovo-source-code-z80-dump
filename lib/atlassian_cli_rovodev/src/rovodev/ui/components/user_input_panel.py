from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.filters import to_filter
from prompt_toolkit.key_binding import KeyBindings, merge_key_bindings
from prompt_toolkit.key_binding.bindings.basic import load_basic_bindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.output import create_output
from pydantic_ai.messages import ModelResponse
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from nemo.constants import DEFAULT_PANEL_WIDTH
from nemo.context import SessionContext
from nemo.utils import fix_live_vertical_overflow
from rovodev.commands.run.command_registry import registry
from rovodev.ui.components.token_display import display_token_usage, get_daily_usage_data

FOOTER_TEXT = '[bright_black]Type "/" for available commands.' + (" " * 64) + "Uses AI. Verify results.[/bright_black]"

console = Console()


async def user_input_panel(
    prompt_session: PromptSession | None = None, session_context: SessionContext | None = None
) -> str:
    buffer = Buffer(multiline=True) if prompt_session is None else prompt_session._create_default_buffer()
    buffer.multiline = to_filter(True)
    kb = KeyBindings()

    @kb.add("c-c")
    def _(event: KeyPressEvent) -> None:
        """Ctrl-C to cancel"""
        event.app.exit(exception=SystemExit(0))

    def accept_suggestion() -> bool:
        """Accept the current suggestion if one exists"""
        if buffer.document.is_cursor_at_the_end and buffer.suggestion and buffer.suggestion.text:
            buffer.insert_text(buffer.suggestion.text)
            return True
        return False

    @kb.add("right")
    def _(event: KeyPressEvent) -> None:
        """Right arrow: accept suggestion if present, otherwise move cursor right"""
        if not accept_suggestion():
            # No suggestion, perform normal right arrow movement
            buffer.cursor_right()

    @kb.add("tab")
    def _(event: KeyPressEvent) -> None:
        """Tab: accept suggestion if present"""
        if not accept_suggestion():
            # No suggestion, insert a tab character
            buffer.insert_text("    ")

    @kb.add("enter")
    def _(event: KeyPressEvent) -> None:
        """Enter to accept or continue input if cursor is after a backslash"""
        doc = event.app.current_buffer.document

        # Check if cursor is after a backslash
        if doc.cursor_position > 0 and doc.text[doc.cursor_position - 1] == "\\":
            # Remove the backslash and add a newline at cursor position
            before_cursor = doc.text[: doc.cursor_position - 1]  # Exclude backslash
            after_cursor = doc.text[doc.cursor_position :]
            buffer.text = before_cursor + "\n" + after_cursor
            buffer.cursor_position = len(before_cursor) + 1  # Position after newline
        else:
            event.app.exit()

    # Create dummy layout for prompt-toolkit
    layout = Layout(Window(BufferControl(buffer=buffer)))

    # Create a custom output that supports bracketed paste mode but does not flush to stdout, since we control output
    # manually with rich
    output = create_output()
    output.enable_bracketed_paste()
    output.flush()
    output.flush = lambda: None

    # Create application with merged key bindings
    app = Application(
        layout=layout,
        output=output,
        key_bindings=merge_key_bindings([load_basic_bindings(), kb]),
        full_screen=False,
        erase_when_done=True,
        mouse_support=False,
    )

    def create_panel() -> Group:
        cursor_line = buffer.document.cursor_position_row
        cursor_column = buffer.document.cursor_position_col

        text = Text()
        buffer_lines = buffer.text.split("\n")

        # Check if cursor is at the end of the last line
        suggestion_text = None
        if cursor_line == len(buffer_lines) - 1 and cursor_column >= len(buffer_lines[-1]):
            suggestion = buffer.suggestion
            if suggestion:
                suggestion_text = suggestion.text

        for i, line in enumerate(buffer_lines):
            if i == 0:
                text.append("> ")
            else:
                text.append("  ")

            if i == cursor_line:
                line_len = len(line)
                line = Text(line)
                if suggestion_text:
                    line.append(Text(suggestion_text, style="dim italic"))
                    line.stylize("reverse", cursor_column, cursor_column + 1)
                elif cursor_column >= line_len:
                    line.append("█")
                else:
                    line.stylize("reverse", cursor_column, cursor_column + 1)

            text.append(line)

            # Add newline if not the last line
            if i < len(buffer_lines) - 1:
                text.append("\n")

        footer = FOOTER_TEXT
        if buffer.text.strip() == "/":
            footer = registry.render_help_table(show_header=False)
        elif buffer.text.strip().startswith("/"):
            try:
                footer = registry.render_help_table(show_header=False, command_filter=buffer.text.strip())
            except ValueError:
                footer = FOOTER_TEXT
        return Group("", Panel(text, width=DEFAULT_PANEL_WIDTH), footer)

    # Display token usage from previous session if available
    if session_context and session_context.usage.total_tokens > 0:
        # Get latest usage from the last response
        responses = [m for m in session_context.message_history if isinstance(m, ModelResponse)]
        if responses:
            latest_usage = responses[-1].usage
            if latest_usage and latest_usage.total_tokens > 0:
                # Get daily usage data upfront to avoid lag between progress bars
                daily_usage_data = get_daily_usage_data()
                display_token_usage(latest_usage.total_tokens, daily_usage_data)
                console.print()  # Add spacing after token display

    with fix_live_vertical_overflow(Live(create_panel(), auto_refresh=False, transient=True)) as live:

        def before_render(_: Application) -> None:
            live.update(create_panel())
            live.refresh()

        app.before_render += before_render
        await app.run_async()

    if buffer.text:
        console.print(f"\n> {buffer.text}", highlight=False)

    # Save to history if prompt_session is not None
    if prompt_session is not None and buffer.text:
        prompt_session.history.append_string(buffer.text)
    return buffer.text
