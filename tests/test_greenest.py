"""Tests the greeenest_window: the sliding-window algorithm, data source faked."""

import pytest

from carbon_mcp import server
from carbon_mcp.carbon_client import CarbonClient

def _slots() -> list[dict]:
    """Ten 30-min slots, all 300 gCO2/kWh, except an obvious dip at index 4-5."""
    values = [300, 300, 300, 300, 50, 50, 300, 300, 300, 300]
    return [
        {
            "from": f"2026-01-01T{i:02d}:00Z",
            "to": f"2026-01-01T{i:02d}:30Z",
            "forecast_gco2_per_kwh":v,
            "index": "low" if v < 100 else "high",
        }
        for i, v in enumerate(values)
    ]

async def fake_forecast(self: CarbonClient, hours: int = 24) -> list[dict]:
    """Drop-in replacement for CarbonClient.forecast - returns our synthetic slots."""
    return _slots()

async def test_greenest_window_finds_the_dip(monkeypatch) -> None:
    # arrange: every CarbonClient.forecast call now returns our fixed slots
    monkeypatch.setattr(CarbonClient, "forecast", fake_forecast)

    # act: .fn calls the raw function, bypassing the MCP tool
    out = await server.greenest_window(duration_hours=1, within_hours=5)
    print(out)

    # assert: a 1h window = 2 slots; the cleanest starts at slot 4
    assert out["start"] == "2026-01-01T04:00Z"
    assert out["mean_forecast_gco2_per_kwh"] == 50.0

async def test_zeroduration_rejected() -> None:
    # the guard runs BEFORE any forecast call, so no monkeypatch needed
    with pytest.raises(ValueError):
        await server.greenest_window(duration_hours=0)
