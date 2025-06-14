"""Custom exceptions and error handling for RovoDev CLI."""

from typing import Any

from humanize import precisedelta

from nemo.constants import DEFAULT_PANEL_WIDTH
from nemo.utils import MCPServerHTTP, MCPServerStdio


class RovoDevError(Exception):
    """Base exception for RovoDev CLI errors."""

    def __init__(self, message: str, title: str = "Error", role: str = "error"):
        super().__init__(message)
        self.message = "\n" + message.strip() + "\n"
        self.title = title
        self.role = role


class UnauthorizedError(RovoDevError):
    """Exception raised when the user is not authorized to perform an action."""

    def __init__(self):
        super().__init__(
            title="You are not authorized to perform this action",
            message="Please check your API key and email address are correct.",
        )


class EntitlementCheckFailed(RovoDevError):
    """Exception raised when an entitlement check fails."""

    def __init__(self, payload: dict[str, Any]):
        status = payload.get("status")
        active_devai_sites = None
        entitlement_params = payload.get("additionalEntitlementParams")
        if entitlement_params:
            active_devai_sites = entitlement_params.get("activeDevAiSites")
        if status == "PRODUCT_NOT_INSTALLED":
            message = (
                "To use Rovo Dev CLI, your organization administrator needs to install Rovo Dev Agents."
                "\n\nVisit https://www.atlassian.com/try/cloud/signup?bundle=devai to request access."
            )
            title = "Rovo Dev Agents is not installed on your site"
        elif status == "CLI_DISABLED":
            if not active_devai_sites:
                message = (
                    "To use Rovo Dev CLI, your organization administrator needs to enable it in Rovo Dev Agents "
                    "settings."
                )
            else:
                message = (
                    "To use Rovo Dev CLI, enable it in Rovo Dev Agents settings.\n\n"
                    f"Visit: {active_devai_sites[0]}/dev-agents/rovo-dev-cli"
                )
            title = "Rovo Dev CLI is not enabled on your site"
        elif status == "USER_NOT_AUTHORIZED":
            message = (
                "To use Rovo Dev CLI, your organization administrator needs to add you to the rovo-dev-agents-users "
                "permission group.\n\nRequest access from your organization administrator."
            )
            title = "You need Rovo Dev Agents user permissions to use Rovo Dev CLI"
        super().__init__(title=title, message=message, role="warning")


class RequestTooLargeError(RovoDevError):
    """Exception raised when the request payload is too large."""

    def __init__(self):
        message = (
            "The request payload is too large. Please run '/prune' to reduce the size of your conversation or start "
            "a new session with the '/sessions' command."
        )
        super().__init__(title="Request Too Large", message=message, role="error")


class RateLimitExceededError(RovoDevError):
    """Exception raised when the rate limit is exceeded."""

    def __init__(self, payload: dict[str, Any]):
        status = payload.get("status")
        balance = payload.get("balance", {})
        daily_total = balance.get("dailyTotal")
        retry_after_seconds = payload.get("retryAfterSeconds")
        if status == "DAILY_LIMIT_EXCEEDED":
            title = "You've reached your daily token limit"
            if daily_total and retry_after_seconds:
                message = (
                    f"Your daily usage limit of {daily_total:,} tokens resets in {precisedelta(retry_after_seconds)}."
                )
            else:
                message = "Your daily usage limit has been exceeded. Please try again later."
        elif status == "MINUTE_LIMIT_EXCEEDED":
            title = "You've reached your minute token limit"
            message = "Please try again later."
        else:
            title = "Rate Limit Exceeded"
            message = "You have exceeded the rate limit for this operation. Please try again later."
        super().__init__(title=title, message=message)


class MCPServerError(RovoDevError):
    """Exception raised for errors related to MCP servers."""

    def __init__(self, title: str, mcp_server: MCPServerHTTP | MCPServerStdio, message: str | None = None):
        """Initialize the MCPServerError with a specific MCP server and title."""
        server_info = self.format_server_info(mcp_server)
        if message:
            message = f"{server_info}\n\n{message}"
        else:
            message = server_info
        super().__init__(title=title, message=message, role="error")

    def format_server_info(self, mcp_server: MCPServerHTTP | MCPServerStdio) -> str:
        """Format the MCP server information for the error message."""
        if isinstance(mcp_server, MCPServerHTTP):
            server_info = f"Failed to start HTTP MCP server at {mcp_server.url}"
        elif isinstance(mcp_server, MCPServerStdio):
            server_info = f"Failed to start STDIO MCP server with command '{' '.join([mcp_server.command] + list(mcp_server.args))}'"
        return (
            server_info if len(server_info) < DEFAULT_PANEL_WIDTH - 4 else f"{server_info[:DEFAULT_PANEL_WIDTH-7]}..."
        )


class MCPServerBuiltinError(MCPServerError):
    """Exception raised for errors related to built-in MCP servers."""

    def __init__(self, mcp_server: MCPServerHTTP | MCPServerStdio):
        super().__init__(
            title="Failed to start built-in MCP server",
            message=(
                "If you continue to see this error, please report it to the Rovo Dev team: "
                "[blue underline]https://rovodevagents.atlassian.net/servicedesk/customer/portal/1/group/1/create/45[/blue underline]"
            ),
            mcp_server=mcp_server,
        )


class MCPServerThirdPartyError(MCPServerError):
    """Exception raised for errors related to third-party MCP servers."""

    def __init__(self, mcp_server: MCPServerHTTP | MCPServerStdio):
        super().__init__(title="Failed to start third-party MCP server", mcp_server=mcp_server)
