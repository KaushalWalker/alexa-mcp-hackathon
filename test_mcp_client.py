import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client


async def main():
    async with streamablehttp_client(
        "http://127.0.0.1:8000/mcp"
    ) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            # 1. Get all tasks
            print("\n1. ALL TASKS")
            result = await session.call_tool(
                "get_tasks", arguments={"status": "all"}
            )
            print(result.content)

            # 2. Get calendar
            print("\n2. CALENDAR")
            result = await session.call_tool("get_calendar")
            print(result.content)

            # 3. Get deadlines
            print("\n3. DEADLINES")
            result = await session.call_tool("get_deadlines")
            print(result.content)

            # 4. Get preferences
            print("\n4. USER PREFERENCES")
            result = await session.call_tool("get_user_preferences")
            print(result.content)

            # 5. Create a test task
            print("\n5. CREATE TASK")
            result = await session.call_tool(
                "create_task",
                arguments={
                    "title": "Test DayPilot MCP tools",
                    "priority": "high",
                    "duration_minutes": 15,
                    "due_date": "2026-10-11",
                },
            )
            print(result.content)


if __name__ == "__main__":
    asyncio.run(main())
