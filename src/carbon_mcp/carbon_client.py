"""Thin async client for the UK Carbon Intensity API (api.carbonintensity.org.uk)."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx  # httpx is a modern async HTTP client for Python

BASE_URL = "https://api.carbonintensity.org.uk"

class CarbonClient:
    """Async wrapper around the Carbon Intensity API.
    
    Holds one httpx.AsyncClient for connection reuse. Caller owns the lifecycle via 'async with'.
    """

    def __init__(self, base_url: str = BASE_URL, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=timeout)

    # Context manager support for automatic cleanup
    async def __aenter__(self) -> CarbonClient:
        return self
    
    # Ensure the HTTP client is properly closed when done
    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    # Internal helper to GET and parse JSON, with error handling
    async def _get(self, path: str) -> dict:
        resp = await self._client.get(path)
        resp.raise_for_status()  # turn HTTP 4xx/5xx into an exception
        return resp.json()  # Return the parsed JSON response
    
    async def current_intensity(self) -> dict:
        """Latest national carbon intensity (gCO2/kWh) and index band."""
        block = (await self._get("/intensity"))["data"][0]
        i = block["intensity"]
        return {
            "from": block["from"],
            "to": block["to"],
            "forecast_gco2_per_kwh": i["forecast"],
            "actual_gco2_per_kwh": i.get("actual"),  # may be null - .get
            "index": i["index"],
        }
    
    async def forecast(self, hours: int = 24) -> list[dict]:
        """Half-hourly forecast for the next 'hours' hours (max 48)."""
        hours = max(1, min(hours, 48))
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
        data = (await self._get(f"/intensity/{now}/fw48h"))["data"]
        slots = data[: hours * 2]  # 30-min resolution -> 2 slots per hour
        return [
            {
                "from": b["from"],
                "to": b["to"],
                "forecast_gco2_per_kwh": b["intensity"]["forecast"],
                "index": b["intensity"]["index"],
            }
            for b in slots
        ]
    
    async def generation_mix(self) -> dict:
        """Current generation mix by fuel (% of total)."""
        block = (await self._get("/generation"))["data"]
        return {
            "from": block["from"],
            "to": block["to"],
            "mix_percent": {m["fuel"]: m["perc"] for m in block["generationmix"]},
        }
