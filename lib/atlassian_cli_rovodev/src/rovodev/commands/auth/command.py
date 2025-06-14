"""The auth command handler for Rovo Dev CLI."""

import typer

app = typer.Typer(
    help="Authentication commands for Rovo Dev CLI", pretty_exceptions_show_locals=False, pretty_exceptions_enable=False
)


@app.command()
def login():
    """Log in to your Atlassian account."""
    # This is a placeholder for this command to populate the help text only.


@app.command()
def logout():
    """Log out of your Atlassian account."""
    # This is a placeholder for this command to populate the help text only.


@app.command()
def status():
    """Show current authentication status."""
    # This is a placeholder for this command to populate the help text only.
