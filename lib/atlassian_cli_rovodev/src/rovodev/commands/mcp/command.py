"""The mcp command handler for Rovo Dev CLI."""

from pathlib import Path

import typer

from rovodev import DEFAULT_MCP_CONFIG_PATH
from rovodev.commands.config.command import open_file_in_editor

app = typer.Typer(pretty_exceptions_show_locals=False, pretty_exceptions_enable=False)


@app.command()
def mcp():
    """Open the Rovo Dev MCP config file in your editor."""
    mcp_config_path = Path(DEFAULT_MCP_CONFIG_PATH)
    if not mcp_config_path.exists() or not mcp_config_path.read_text().strip():
        mcp_config_path.parent.mkdir(parents=True, exist_ok=True)
        mcp_config_path.write_text('{\n    "mcpServers": {}\n}')
    return open_file_in_editor(DEFAULT_MCP_CONFIG_PATH)
