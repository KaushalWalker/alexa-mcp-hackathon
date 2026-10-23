# DayPilot — Developer Friction Log

## 1. MCP Server Startup and Python Module Imports

**Task:** Start the DayPilot MCP server locally.

**What I tried:** Running `python app\server\mcp_server.py` directly.

**Expected result:** The MCP server starts successfully.

**Actual result:** Python could not resolve the `app` package and raised `ModuleNotFoundError`.

**Resolution:** Running the server as a module with `python -m app.server.mcp_server` resolved the import issue.

**Severity:** Medium.

**Suggested improvement:** MCP project templates should clearly document the correct launch command and expected working directory.

## 2. Verifying MCP Tool Discovery

**Task:** Confirm that DayPilot exposes its planning and task-management tools through MCP.

**What I tried:** Starting the server and testing it through a Python MCP client.

**Expected result:** The client initializes successfully and discovers the available tools.

**Actual result:** A server starting successfully did not, by itself, prove that the tools were discoverable and callable.

**Resolution:** I used an MCP client session to initialize the connection and verify tool discovery.

**Severity:** Medium.

**Suggested improvement:** Provide clearer examples for testing MCP connections, listing tools, and validating tool calls during local development.

## 3. Natural-Language Planning and Response Quality

**Task:** Turn everyday planning requests into useful daily schedules and task actions.

**What I tried:** Testing natural-language requests through the DayPilot interface and iterating on assistant behavior.

**Expected result:** The assistant should interpret the request correctly and return a clear, actionable response.

**Actual result:** Natural-language behavior required additional testing and debugging to improve consistency.

**Resolution:** I iterated on the assistant logic and tested the resulting behavior.

**Severity:** Medium.

**Suggested improvement:** Provide practical evaluation examples for common voice-assistant intents, ambiguous requests, and planning edge cases.

## Summary

Building DayPilot helped me understand the practical work involved in connecting an AI planning interface with MCP tools. The biggest lessons were to document reliable startup commands, verify tool discovery independently, and test natural-language behavior rather than relying on a successful server startup alone.

DayPilot currently runs locally. Live Alexa+ device integration has not been implemented.
