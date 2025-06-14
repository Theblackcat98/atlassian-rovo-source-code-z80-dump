"""The log command handler for Rovo Dev CLI."""

import typer

from rovodev import DEFAULT_LOG_PATH
from rovodev.commands.config.command import open_file_in_editor

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_enable=False)


@app.command()
def log():
    """Open the Rovo Dev log file in your editor."""
    return open_file_in_editor(DEFAULT_LOG_PATH)
