"""Carbon-aware MCP server: live UK grid carbon-intensity tools for agents."""

from __future__ import annotations

import os

from fastmcp import FastMCP

from carbon_mcp.carbon_client import CarbonClient

mcp = FastMCP(name="carbon-aware-mcp")

@mcp.tool
async def current_intensity() -> dict:
    """Current UK national grid carbon intensity (gCO2/kWh) and its index band."""
    async with CarbonClient() as client:
        return await client.current_intensity()
    
def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    mcp.run(transport="http", host="0.0.0.0", port=port)

if __name__  == "__main__":
    main()