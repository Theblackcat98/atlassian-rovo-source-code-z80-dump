from pathlib import Path

import pytest
from pydantic_ai import Agent

from nemo.utils import MCPServerStdio
from rovodev.common.exceptions import MCPServerBuiltinError, MCPServerThirdPartyError
from rovodev.modules.mcp_utils import run_mcp_servers_with_error_handling


@pytest.mark.asyncio
async def test_run_mcp_servers_with_error_handling():
    """Test the `run_mcp_servers_with_error_handling` function."""
    mcp_server_file = Path(__file__).parent.parent / "mcp_server.py"
    agent = Agent(mcp_servers=[MCPServerStdio(command="python", args=[str(mcp_server_file)])])

    async with run_mcp_servers_with_error_handling(agent):
        pass


@pytest.mark.asyncio
async def test_run_mcp_servers_with_third_party_error_handling():
    """Test the `run_mcp_servers_with_error_handling` function with a failing MCP server."""
    mcp_server_file = Path(__file__).parent.parent / "mcp_server.py"
    with pytest.raises(MCPServerThirdPartyError) as exc_info:
        # Simulate a failure in the MCP server
        agent = Agent(mcp_servers=[MCPServerStdio(command="python", args=[str(mcp_server_file), "fail"])])
        async with run_mcp_servers_with_error_handling(agent):
            pass

    assert f"Failed to start STDIO MCP server with command 'python" in str(exc_info.value)


@pytest.mark.asyncio
async def test_run_mcp_servers_with_builtin_error_handling():
    """Test the `run_mcp_servers_with_error_handling` function with a built-in MCP server."""
    mcp_server_file = Path(__file__).parent.parent / "mcp_server.py"
    with pytest.raises(MCPServerBuiltinError) as exc_info:
        # Simulate a failure in the MCP server
        agent = Agent(mcp_servers=[MCPServerStdio(command="python", args=[str(mcp_server_file), "fail", "nautilus"])])
        async with run_mcp_servers_with_error_handling(agent):
            pass

    assert f"Failed to start STDIO MCP server with command 'python" in str(exc_info.value)
