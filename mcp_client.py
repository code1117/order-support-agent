

"""Connect to the local MCP server and call its order-support tools."""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client


MCP_SERVER_PATH = Path(__file__).with_name("mcp_server.py")


def get_result_text(result: types.CallToolResult) -> str:
    """Extract readable text from an MCP tool result."""

    for content in result.content:
        if isinstance(content, types.TextContent):
            return content.text

    return "The MCP tool returned no readable content."


async def call_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    ticket_customer_id: str,
) -> dict[str, Any]:
    """Call one MCP tool using the current ticket's trusted customer ID."""

    server_environment = os.environ.copy()
    server_environment["TICKET_CUSTOMER_ID"] = ticket_customer_id

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(MCP_SERVER_PATH)],
        env=server_environment,
    )

    async with stdio_client(server_parameters) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            try:
                result = await session.call_tool(
                    tool_name,
                    arguments=arguments,
                )
            except Exception as error:
                return {
                    "ok": False,
                    "error": str(error),
                }

    result_text = get_result_text(result)

    if result.isError:
        return {
            "ok": False,
            "error": result_text,
        }

    try:
        result_data = json.loads(result_text)
    except json.JSONDecodeError:
        result_data = result_text

    return {
        "ok": True,
        "data": result_data,
    }


def run_mcp_tool(
    tool_name: str,
    arguments: dict[str, Any],
    ticket_customer_id: str,
) -> dict[str, Any]:
    """Call an MCP tool from ordinary synchronous Python code."""

    return asyncio.run(
        call_mcp_tool(
            tool_name=tool_name,
            arguments=arguments,
            ticket_customer_id=ticket_customer_id,
        )
    )