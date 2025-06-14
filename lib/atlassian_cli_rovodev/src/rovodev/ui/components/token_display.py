"""Token usage display components for the CLI."""

from typing import Any, Dict

from rich.console import Console

import nemo
from rovodev.modules.sessions import default_context_limit
from rovodev.modules.usage import get_usage

console = Console()


def get_daily_usage_data() -> Dict[str, Any] | None:
    """Get daily usage data upfront to avoid lag during display.

    Returns:
        Dictionary with daily usage data or None if not available
    """
    try:
        if nemo.AUTH_METHOD == "api_token":
            usage_data = get_usage()
            balance = usage_data.get("balance", {})
            daily_used = balance.get("dailyUsed", 0)
            daily_total = balance.get("dailyTotal", 0)

            if daily_total > 0:
                return {
                    "daily_used": daily_used,
                    "daily_total": daily_total,
                }
    except Exception:
        # Silently fail if we can't get usage data
        pass

    return None


def format_tokens(tokens: int) -> str:
    """Format token count in human-readable format (K/M)."""
    if tokens >= 1_000_000:
        formatted = f"{tokens / 1_000_000:.1f}M"
    elif tokens >= 1_000:
        formatted = f"{tokens / 1_000:.1f}K"
    else:
        formatted = str(tokens)

    # Remove .0 from whole numbers
    if formatted.endswith(".0K"):
        formatted = formatted[:-3] + "K"
    elif formatted.endswith(".0M"):
        formatted = formatted[:-3] + "M"

    return formatted


def display_token_usage(tokens: int, daily_usage_data: Dict[str, Any] | None = None) -> None:
    """Display token usage with progress bars matching session list style.

    Args:
        tokens: Current session token count
        daily_usage_data: Pre-fetched daily usage data to avoid network lag
    """
    context_limit = default_context_limit
    context_proportion = min(tokens / context_limit, 1)
    width = 10  # Same width as session list for consistency
    filled = int(context_proportion * width)
    unfilled = width - filled

    # Display session context usage (using console.print with separate parts)
    context_bar = (
        "[dim]Session context: [/dim][bold blue]" + "▮" * filled + "[/bold blue][dim]" + "▮" * unfilled + "[/dim]"
    )

    if context_proportion > 0.5:
        console.print(
            context_bar,
            f"[reset][dim]{format_tokens(tokens)}/{format_tokens(context_limit)}[/dim][/reset]",
            "[dim]| [bold]Tip:[/bold] use the [reset]/prune[/reset] command to reduce context size[/dim]",
        )
    else:
        console.print(
            context_bar,
            f"[reset][dim]{format_tokens(tokens)}/{format_tokens(context_limit)}[/dim][/reset]",
        )

    # Display daily usage if data is available
    if daily_usage_data:
        daily_used = daily_usage_data["daily_used"]
        daily_total = daily_usage_data["daily_total"]
        daily_proportion = min(daily_used / daily_total, 1)
        daily_filled = int(daily_proportion * width)
        daily_unfilled = width - daily_filled

        # Display daily usage (using console.print with separate parts)
        daily_bar = (
            "[dim]Daily total:     [/dim][bold blue]"
            + "▮" * daily_filled
            + "[/bold blue][dim]"
            + "▮" * daily_unfilled
            + "[/dim]"
        )
        console.print(
            daily_bar,
            f"[reset][dim]{format_tokens(daily_used)}/{format_tokens(daily_total)}[/dim][/reset]",
        )
