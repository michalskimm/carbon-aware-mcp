import asyncio
import os

from fastmcp import Client

# URL defaults to local; override for cloud with: MCP_URL=https://...azurecontainerapps.io/mcp
mcp_url = os.getenv("MCP_URL", "http://localhost:8000/mcp")

# keep token short-lived and rotate regularly; set from gen_keys.py output; fail fast if not set
client_token = os.environ["CARBON_MCP_TOKEN"]


async def main() -> None:
    async with Client(mcp_url, auth=client_token) as c:
        print(f"connected to: {mcp_url}")
        print("tools:", [t.name for t in await c.list_tools()])
        print("now:", (await c.call_tool("current_intensity", {})).data)
        print("greenest:", (await c.call_tool("greenest_window", {"duration_hours": 3})).data)


asyncio.run(main())