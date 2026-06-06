import asyncio

from fastmcp import Client

async def main() -> None:
    async with Client("http://localhost:8000/mcp") as c:
        print("tools:", [t.name for t in await c.list_tools()])
        print("now:", (await c.call_tool("current_intensity", {})).data)
        print("greenest:", (await c.call_tool("greenest_window", {"duration_hours": 3})).data)

asyncio.run(main())