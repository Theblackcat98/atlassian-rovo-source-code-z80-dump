from prompt_toolkit import PromptSession as PromptSessionPT
from prompt_toolkit.history import FileHistory

from nemo.constants import DEFAULT_EXIT_COMMANDS
from nemo.context import SessionContext
from rovodev.commands.run.command_registry import registry
from rovodev.ui.components.user_input_panel import user_input_panel


class PromptSession(PromptSessionPT):
    """Custom PromptSession class to handle user input."""

    def prompt_async(self, *args, session_context: SessionContext | None = None, **kwargs):
        """Override the prompt_async method to use a custom user input panel."""
        return user_input_panel(self, session_context)


class FilteredFileHistory(FileHistory):
    """Custom FileHistory class to filter out unwanted entries."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_string = None

    @property
    def last_string(self) -> str:
        """Return the last string provided by the user (whether or not it was added to history)."""
        return self._last_string or ""

    def append_string(self, string):
        """Append a string to the history, but filter out unwanted entries."""
        self._last_string = string
        if not string.strip() or string in DEFAULT_EXIT_COMMANDS:
            return
        return super().append_string(string)

    def load_history_strings(self):
        """Load history strings, ensuring that all slash commands are present."""
        return list(super().load_history_strings()) + registry.commands
