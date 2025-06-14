"""Command instrumentation utilities."""

from contextlib import contextmanager

import logfire
from loguru import logger


@contextmanager
def track_command(command: str, sub_command: str | None = None):
    """
    Track a command execution using a single span.

    Args:
        command: The command being executed (e.g., "/sessions", "/memory")
        sub_command: Optional subcommand (e.g., "init" for "/memory init")

    Usage:
        with track_command("/sessions", "list") as span:
            # Execute command
            result = do_something()
            # Optionally set additional attributes
            span.set_attribute("some_metric", value)
    """
    logger.debug(f"About to create span for command: {command}")
    with logfire.span("command executed") as span:
        # Set initial attributes
        span.set_attribute("command_name", command)
        if sub_command:
            span.set_attribute("sub_command", sub_command)

        try:
            # Let the command execute
            yield span
            # If we get here, command succeeded
            span.set_attribute("success", True)
        except Exception as e:
            # Command failed
            span.set_attribute("success", False)
            span.set_attribute("error", str(e))
            raise
