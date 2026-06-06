"""Carbon-aware MCP server: live UK grid carbon-intensity tools for agents."""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier  # JSON Web Token

from carbon_mcp.carbon_client import CarbonClient

# load env
public_key = os.environ["CARBON_MCP_PUBLIC_KEY"].replace("\\n", "\n")  # fail fast if not set

ISSUER, AUDIENCE = "http://carbon-aware-mcp", "carbon-aware-mcp"

auth = JWTVerifier(
    public_key=public_key,
    issuer=ISSUER,
    audience=AUDIENCE,
    required_scopes={"read"},
)

mcp = FastMCP(name="carbon-aware-mcp", auth=auth)

@mcp.tool
async def current_intensity() -> dict:
    """Current UK national grid carbon intensity (gCO2/kWh) and its index band."""
    async with CarbonClient() as client:
        return await client.current_intensity()
    
@mcp.tool
async def forecast(hours: int = 24) -> list[dict]:
    """Half-hourly carbon-intensity forecast for the next 'hours' hours (1-48)."""
    async with CarbonClient() as client:
        return await client.forecast(hours)
    
@mcp.tool
async def generation_mix() -> dict:
    """Current gen mix by fuel type, as %s of total."""
    async with CarbonClient() as client:
        return await client.generation_mix()
    
@mcp.tool
async def greenest_window(duration_hours: int, within_hours: int = 24) -> dict:
    """Find the lowest-average-carbon continous window of 'duration_hours' starting within the next 'within_hours'. 
    Use this to schedule workload.
    
    Returns the chosen windows start/end and its mean forecast intensity.
    """
    if duration_hours < 1:
        raise ValueError("duration_hours must be >= 1")
    async with CarbonClient() as client:
        slots = await client.forecast(within_hours)

    width = duration_hours * 2  # 30-min slots
    if width > len(slots):
        raise ValueError("duration_hours exceed available forecast horizon")
    
    best_start, best_avg = 0, float("inf")
    for i in range(len(slots) - width + 1):
        window = slots[i : i + width]
        avg = sum(s["forecast_gco2_per_kwh"] for s in window) / width
        if avg < best_avg:
            best_start, best_avg = i, avg

    chosen = slots[best_start : best_start + width]
    return {
        "start": chosen[0]["from"],
        "end": chosen[-1]["to"],
        "mean_forecast_gco2_per_kwh": round(best_avg, 1),
        "duration_hours": duration_hours,
    }
    
def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    mcp.run(transport="http", host="0.0.0.0", port=port)

if __name__  == "__main__":
    main()