
import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8000/mcp"
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools = await session.list_tools()
            names = [tool.name for tool in tools.tools]

            print("AVAILABLE TOOLS:", names)
            assert "generate_daily_plan" in names

            result = await session.call_tool(
                "generate_daily_plan",
                arguments={"plan_date": "2026-10-12"},
            )

            if result.isError:
                raise RuntimeError(result.content)

            if result.structuredContent:
                plan = result.structuredContent
            else:
                plan = json.loads(result.content[0].text)

            print("\nDAYPILOT PLAN VIA MCP")
            print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
