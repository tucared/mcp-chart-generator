#!/usr/bin/env python3
"""
MCP Chart Generator Server

A Model Context Protocol server that generates PNG charts from Vega-Lite specifications.
"""

import logging
import sys
from pathlib import Path

import altair as alt
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .tools import (
    ChartRequest,
    DEFAULT_OUTPUT_DIR,
    get_tool_definitions,
)

# Configure logging to stderr to avoid interfering with MCP communication
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-chart-generator")

# Create the MCP server
server = Server("mcp-chart-generator")


@server.list_tools()
async def list_tools():
    """List available tools."""
    return get_tool_definitions()


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Handle tool calls."""
    if name != "generate_chart":
        raise ValueError(f"Unknown tool: {name}")

    try:
        # Parse and validate the request
        request = ChartRequest(**arguments)

        # Set up output path
        if request.output_path:
            output_path = Path(request.output_path)
        else:
            DEFAULT_OUTPUT_DIR.mkdir(exist_ok=True)
            output_path = DEFAULT_OUTPUT_DIR / "chart.png"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create Altair chart from Vega-Lite spec
        chart = alt.Chart.from_dict(request.vega_lite_spec)

        # Save the chart as PNG
        chart.save(str(output_path))

        logger.info(f"Successfully generated chart: {output_path}")

        return [
            TextContent(
                type="text",
                text=f"Chart successfully generated and saved to: {output_path.absolute()}",
            )
        ]

    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        return [TextContent(type="text", text=f"Error generating chart: {str(e)}")]


def main():
    """Main entry point for the server."""
    import asyncio

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
