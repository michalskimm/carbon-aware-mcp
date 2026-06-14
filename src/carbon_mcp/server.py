"""Carbon-aware MCP server: live UK grid carbon-intensity tools for agents."""

from __future__ import annotations

import os

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier  # JSON Web Token
from starlette.requests import Request
from starlette.responses import HTMLResponse

from carbon_mcp.carbon_client import CarbonClient
from carbon_mcp.observability import ObservabilityMiddleware, configure_observability

public_key = os.environ["CARBON_MCP_PUBLIC_KEY"].replace("\\n", "\n")  # fail fast if not set

configure_observability()  # set up logging + tracing before anything else

ISSUER, AUDIENCE = "http://carbon-aware-mcp", "carbon-aware-mcp"

auth = JWTVerifier(
    public_key=public_key,
    issuer=ISSUER,
    audience=AUDIENCE,
    required_scopes={"read"},
)

mcp = FastMCP(name="carbon-aware-mcp", auth=auth, middleware=[ObservabilityMiddleware()])


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
    """Find the lowest-average-carbon contiguous window of `duration_hours`
      starting within the next `within_hours`. Use this to schedule a workload.

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


@mcp.custom_route("/", methods=["GET"])
async def landing(request: Request) -> HTMLResponse:
    """Human-friendly landing page so the base URL isn't a bare 405."""
    return HTMLResponse(
        """<!doctype html>
<html><head><meta charset="utf-8"><title>carbon-aware-mcp</title>
<style>
  body{font-family:system-ui,-apple-system,sans-serif;max-width:42rem;margin:4rem auto;
       padding:0 1.5rem;line-height:1.6;color:#2c2c2a}
  code{background:#f1efe8;padding:.15rem .4rem;border-radius:4px}
  a{color:#0f6e56}
  .tag{color:#5f5e5a;font-size:.9rem}
</style></head>
<body>
  <h1>carbon-aware-mcp <span class="tag">v0.1.0</span></h1>
  <p>A remote <a href="https://modelcontextprotocol.io">MCP</a> server exposing live UK
  grid carbon-intensity tools, so an LLM agent can schedule workloads when the grid is
  cleanest.</p>
  <p><strong>Status:</strong> live ✓ &nbsp;·&nbsp; <strong>MCP endpoint:</strong>
  <code>/mcp</code> (JWT-authenticated, POST-only — not browseable)</p>
  <p>Tools: <code>current_intensity</code>, <code>forecast</code>,
  <code>generation_mix</code>, <code>greenest_window</code>.</p>
  <p class="tag">Source &amp; docs:
  <a href="https://github.com/michalskimm/carbon-aware-mcp">github.com/michalskimm/carbon-aware-mcp</a></p>
</body></html>"""
    )


def main() -> None:
    port = int(os.getenv("PORT", "8000"))
    mcp.run(transport="http", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
