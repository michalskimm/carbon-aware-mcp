# carbon-aware-mcp/scripts/probe_api_limits.py
"""Verify the UK Carbon Intensity API behaves as carbon_client assumes.

NOT an eval — exploratory, no pass/fail. Lives in the mcp repo (native import, no
cross-repo coupling; the eval repo encodes the confirmed numbers as rubric constants).

The *limits are already explicit in carbon_client.py*: forecast clamps to 48h (min(hours,48),
upstream fw48h), and greenest_window takes whole `duration_hours`, raising when the window
exceeds the (clamped) search horizon. This script confirms the upstream matches those
assumptions — slot counts, the clamp, the raise — rather than discovering unknowns.

    uv run python scripts/probe_api_limits.py
"""

from __future__ import annotations

import asyncio

from carbon_mcp.carbon_client import CarbonClient
from carbon_mcp.server import greenest_window


async def probe_forecast_slots() -> None:
    """Confirm 30-min resolution (2 slots/hour) and the hard 48h clamp."""
    print("\n== forecast: slot counts vs requested hours ==")
    async with CarbonClient() as client:
        for hours in (1, 6, 24, 48, 72, 96):  # 72/96 should clamp to 48h worth of slots
            slots = await client.forecast(hours)
            expected = min(hours, 48) * 2
            flag = "ok" if len(slots) == expected else "MISMATCH"
            print(f"  req {hours:>3}h -> {len(slots):>3} slots (expect {expected:>3}) [{flag}]")


async def probe_greenest_window_boundary() -> None:
    """Find where greenest_window raises: duration_hours > within_hours."""
    print("\n== greenest_window: duration vs within_hours (default within=24 -> raises >24) ==")
    for duration in (1, 6, 12, 24, 25, 48, 49):
        try:
            res = await greenest_window(duration_hours=duration)  # within_hours defaults to 24
            print(
                f"  {duration:>3}h -> OK   "
                f"start={res['start']} mean={res['mean_forecast_gco2_per_kwh']}"
            )
        except ValueError as e:
            print(f"  {duration:>3}h -> RAISE ValueError: {e}")
    print("\n== same, within_hours=48 (-> raises >48) ==")
    for duration in (24, 48, 49):
        try:
            res = await greenest_window(duration_hours=duration, within_hours=48)
            print(f"  {duration:>3}h -> OK   mean={res['mean_forecast_gco2_per_kwh']}")
        except ValueError as e:
            print(f"  {duration:>3}h -> RAISE ValueError: {e}")


async def main() -> None:
    await probe_forecast_slots()
    await probe_greenest_window_boundary()
    print("\nConfirmed boundaries -> encode in eval limits-* rubrics + README Decision log.")


if __name__ == "__main__":
    asyncio.run(main())
