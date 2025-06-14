import sys

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Rovo Dev CLI Test MCP Server")


@mcp.tool()
async def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit.

    Args:
        celsius: Temperature in Celsius

    Returns:
        Temperature in Fahrenheit
    """
    return (celsius * 9 / 5) + 32


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "fail":
        # Simulate a failure in the MCP server
        raise RuntimeError("Simulated failure in MCP server")
    mcp.run()
