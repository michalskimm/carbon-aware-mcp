"""Tests for CarbonClient: correct parsing of the API response, network mocked."""

import respx  # library for mocking HTTP requests

from carbon_mcp.carbon_client import CarbonClient

BASE = "https://api.carbonintensity.org.uk"

@respx.mock
async def test_current_intensity_parses() -> None:
    # arrange: inercept the GET and return JSON we control
    respx.get(f"{BASE}/intensity").respond(
        json={
            "data": [
                {
                    "from": "2026-01-01T00:00Z",
                    "to": "2026-01-01T00:30Z",
                    "intensity": {"forecast": 120, "actual": 115, "index": "moderate"}
                }
            ]
        }
    )

    # act
    async with CarbonClient() as client:
        out = await client.current_intensity()

    # assert: the shape MY code produces, not API's raw shape
    assert out['forecast_gco2_per_kwh'] == 120
    assert out['actual_gco2_per_kwh'] == 115
    assert out['index'] == "moderate"

@respx.mock
async def test_current_intensity_handles_null_actual() -> None:
    respx.get(f"{BASE}/intensity").respond(
        json={
            "data": [
                {
                    "from": "2026-01-01T00:00Z",
                    "to": "2026-01-01T00:30Z",
                    "intensity": {"forecast": 90, "actual": None, "index": "low"}
                }
            ]
        }
    )
    async with CarbonClient() as client:
        out = await client.current_intensity()

    assert out["actual_gco2_per_kwh"] is None # the bug .get() prevents



