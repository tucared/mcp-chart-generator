#!/usr/bin/env python3
"""
MCP Chart Generator Server

A Model Context Protocol server that generates PNG charts from Vega-Lite specifications.
"""

import argparse
import logging
import sys
from pathlib import Path

import altair as alt
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .tools import (
    ChartRequest,
    get_tool_definitions,
    sanitize_chart_title,
    set_default_output_dir,
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

        # Sanitize chart title for directory name
        safe_title = sanitize_chart_title(request.chart_title)

        # Set up output path
        if request.output_path:
            output_path = Path(request.output_path)
        else:
            from .tools import get_default_output_dir

            default_dir = get_default_output_dir()
            chart_dir = default_dir / safe_title
            chart_dir.mkdir(parents=True, exist_ok=True)
            output_path = chart_dir / "graph.png"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add title to Vega-Lite spec
        vega_spec = request.vega_lite_spec.copy()
        vega_spec["title"] = request.chart_title

        # Create Altair chart from Vega-Lite spec
        chart = alt.Chart.from_dict(vega_spec)

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

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="MCP Chart Generator Server")
    parser.add_argument(
        "--output-dir",
        type=str,
        required=True,
        help="Output directory for generated charts",
    )
    args = parser.parse_args()

    # Set the output directory
    set_default_output_dir(Path(args.output_dir))
    logger.info(f"Using output directory: {args.output_dir}")

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
