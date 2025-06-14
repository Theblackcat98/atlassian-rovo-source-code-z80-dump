from loguru import logger

from nemo.utils.logging import InteractiveMessageHandler
from rovodev import IS_INTERNAL_USER


def log_file_filter(record) -> bool:
    """Filter to only log records to handle streaming."""
    # If stream_end is None, just call the parent emit method
    stream_end = record.get("extra", {}).get("stream_end")
    if stream_end is None:
        if record["level"].no >= logger.level("INFO").no:
            # Log INFO and above messages for everyone
            return True
        if record["level"].no <= logger.level("DEBUG").no and IS_INTERNAL_USER:
            # Log DEBUG messages only for internal users
            return True
        return False

    # If stream_end is present but False, skip the record
    if not stream_end:
        return False

    # Otherwise, combine stream_content with the message and log
    stream_content = record.get("extra", {}).get("stream_content")
    if stream_content:
        record["message"] = f"{stream_content}{record['message']}"
    return True


def setup_logging(
    log_file: str,
    output_format: str = "markdown",
    show_tool_results: bool = True,
    interactive: bool = True,
) -> None:
    """Set up logging for the application."""
    logger.remove()
    if interactive:
        logger.add(
            InteractiveMessageHandler(
                output_format=output_format,  # type: ignore
                show_tool_results=show_tool_results,
                stream_footer_text=" [bright_black]ctrl+c to interrupt[/bright_black]",
            )
        )

    logger.add(
        log_file,
        mode="a",
        rotation="10 MB",
        compression="gz",
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | - <level>{message}</level>",
        filter=log_file_filter,
    )
