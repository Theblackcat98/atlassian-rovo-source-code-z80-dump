"""The config command handler for Rovo Dev CLI."""

import os
import shutil
import subprocess
from pathlib import Path

import rich
import typer
from loguru import logger

from rovodev import DEFAULT_CONFIG_PATH

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_enable=False)


@app.command()
def config():
    """Open the Rovo Dev configuration file in your editor."""
    return open_file_in_editor(DEFAULT_CONFIG_PATH)


def detect_editor() -> str | None:
    """Detect the editor to use based on the environment."""
    # Check if running in Cursor terminal
    if os.environ.get("__CFBundleIdentifier") == "com.todesktop.230313mzl4w4u92" or os.environ.get("CURSOR_TRACE_ID"):
        return "cursor"

    # TODO: Check if running in Windsurf terminal

    # Check if running in VSCode terminal
    if (
        os.environ.get("__CFBundleIdentifier") == "com.microsoft.VSCode"
        or os.environ.get("VSCODE_PROFILE_INITIALIZED")
        or os.environ.get("VSCODE_INJECTION")
    ):
        return "code"

    # Check if running in JetBrains terminal
    if os.environ.get("__CFBundleIdentifier") == "com.jetbrains.intellij":
        return "idea"

    return None


def open_file_in_editor(file_path: str):
    """Open a file in the user's editor."""
    # Ensure file exists
    config_path = Path(file_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if not config_path.exists():
        config_path.touch()

    editor = detect_editor()
    if not editor or not shutil.which(editor):
        editor = os.environ.get("EDITOR")

    if not editor:
        rich.print(
            "[yellow]Could not detect editor. Please set the EDITOR environment variable or open the file manually: "
            f"{config_path}[/yellow]"
        )
        return

    # Open the file in the editor
    try:
        subprocess.run([editor, str(config_path)], check=True)
    except subprocess.CalledProcessError as e:
        rich.print(f"[yellow]Failed to open file '{str(config_path)}' in the editor '{editor}'[/yellow]")
