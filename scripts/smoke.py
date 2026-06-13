import asyncio
import os

from fastmcp import Client

# keep token short-lived and rotate regularly; set from gen_keys.py output; fail fast if not set
client_token = os.environ["CARBON_MCP_TOKEN"]


async def main() -> None:
    async with Client("http://localhost:8000/mcp", auth=client_token) as c:
        print("tools:", [t.name for t in await c.list_tools()])
        print("now:", (await c.call_tool("current_intensity", {})).data)
        print("greenest:", (await c.call_tool("greenest_window", {"duration_hours": 3})).data)


asyncio.run(main())
