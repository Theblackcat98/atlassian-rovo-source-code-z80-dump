"""Utilities for reporting usage statistics."""

from typing import Any

import httpx
import humanize
import rich
from loguru import logger
from rich import box
from rich.console import Console
from rich.panel import Panel

import nemo
from nemo.constants import DEFAULT_PANEL_WIDTH
from nemo.utils.ai_gateway import get_ai_gateway_headers
from rovodev.common.exceptions import EntitlementCheckFailed, RovoDevError, UnauthorizedError

console = Console()

USAGE_TEMPLATE = """\
[bold]Today's Token Balance[/bold]
[bright_black]\
Your token balance will reset every day at midnight UTC time.

Total Allowed:      {daily_total}
Remaining Balance:  {daily_remaining}
Used Today:         {daily_used}\
[/bright_black]\
"""


def get_usage() -> dict[str, Any] | str:
    """Fetch the current usage statistics from the API."""
    for _ in range(3):
        try:
            timeout = httpx.Timeout(20.0)
            headers = get_ai_gateway_headers()
            response = httpx.get(
                "https://api.atlassian.com/rovodev/v2/credits/check",
                timeout=timeout,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
            break
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise UnauthorizedError()
            # For all other request errors, we retry
            logger.warning(f"Request error: {e}. Retrying...")
        except httpx.RequestError as e:
            # For all other request errors, we retry
            logger.warning(f"Request error: {e}. Retrying...")
    else:
        logger.error("Failed to connect to the Rovo Dev API after multiple attempts.")
        raise RovoDevError(f"Failed to connect to the Rovo Dev API, please try again later.")

    if data.get("status") in ["PRODUCT_NOT_INSTALLED", "CLI_DISABLED", "USER_NOT_AUTHORIZED"]:
        raise EntitlementCheckFailed(payload=data)

    return data


def handle_usage_command() -> str | None:
    """Handle the /usage command."""
    if nemo.AUTH_METHOD != "api_token":
        return "/usage is only available when using API_TOKEN authentication."

    data = get_usage()
    balance = data.get("balance", {})
    daily_total = balance.get("dailyTotal", 0)
    daily_remaining = balance.get("dailyRemaining", 0)
    daily_used = balance.get("dailyUsed", 0)
    retry_after_seconds = data.get("retryAfterSeconds")

    usage_text = USAGE_TEMPLATE.format(
        daily_total=f"{daily_total:,}",
        daily_remaining=f"{daily_remaining:,}",
        daily_used=f"{daily_used:,}",
    )

    if retry_after_seconds and daily_remaining == 0:
        time_to_reset = humanize.precisedelta(retry_after_seconds)
        usage_text += f"\n\nYour daily token allowance resets in {time_to_reset}."

    rich.print(Panel(usage_text, width=DEFAULT_PANEL_WIDTH, box=box.SIMPLE))
    return
