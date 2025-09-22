#!/usr/bin/env python3
"""
MCP Chart Generator Server

A Model Context Protocol server that generates PNG charts from Vega-Lite specifications.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import altair as alt
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .tools import (
    ChartRequest,
    chart_exists,
    get_chart_directory,
    get_default_output_format,
    get_tool_definitions,
    sanitize_chart_title,
    set_default_output_dir,
    set_default_output_format,
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
    if name == "create_chart":
        return await handle_create_chart(arguments)
    elif name == "list_charts":
        return await handle_list_charts(arguments)
    elif name == "get_chart_config":
        return await handle_get_chart_config(arguments)
    elif name == "get_chart_data":
        return await handle_get_chart_data(arguments)
    elif name == "set_chart_config":
        return await handle_set_chart_config(arguments)
    elif name == "set_chart_data":
        return await handle_set_chart_data(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


async def regenerate_chart(chart_name: str) -> bool:
    """Regenerate a chart from its saved config and data files."""
    try:
        chart_dir = get_chart_directory(chart_name)
        config_file = chart_dir / "vega_lite_config.json"
        data_file = chart_dir / "data.json"

        # Load the config
        with open(config_file, "r", encoding="utf-8") as f:
            vega_spec = json.load(f)

        # Load the data if it exists and merge it into the spec
        if data_file.exists():
            with open(data_file, "r", encoding="utf-8") as f:
                data_values = json.load(f)
            # Replace the data.url reference with actual values for rendering
            vega_spec["data"] = {"values": data_values}

        # Determine the output format by checking existing files
        output_format = get_default_output_format()
        for fmt in ["svg", "png", "pdf"]:
            if (chart_dir / f"graph.{fmt}").exists():
                output_format = fmt
                break

        # Create output path
        output_path = chart_dir / f"graph.{output_format}"

        # Create Altair chart from the merged spec
        chart = alt.Chart.from_dict(vega_spec)

        # Save the regenerated chart
        chart.save(str(output_path))

        logger.info(
            f"Successfully regenerated {output_format.upper()} chart: {output_path}"
        )
        return True

    except Exception as e:
        logger.error(f"Error regenerating chart '{chart_name}': {str(e)}")
        return False


async def handle_create_chart(arguments: dict):
    """Handle create_chart tool calls."""
    try:
        # Parse and validate the request
        request = ChartRequest(**arguments)

        # Sanitize chart title for directory name
        safe_title = sanitize_chart_title(request.chart_title)

        # Determine output format
        output_format = request.output_format or get_default_output_format()

        # Set up output path
        if request.output_path:
            base_path = Path(request.output_path)
            # Remove extension if provided to create base path
            if base_path.suffix:
                base_path = base_path.with_suffix("")
            output_path = base_path.with_suffix(f".{output_format}")
        else:
            from .tools import get_default_output_dir

            default_dir = get_default_output_dir()
            chart_dir = default_dir / safe_title
            chart_dir.mkdir(parents=True, exist_ok=True)
            output_path = chart_dir / f"graph.{output_format}"

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Add title to Vega-Lite spec
        vega_spec = request.vega_lite_spec.copy()
        vega_spec["title"] = request.chart_title

        # Extract data if embedded and save separately
        data_path = None
        data_values = None
        if "data" in vega_spec and "values" in vega_spec["data"]:
            # Extract the data values
            data_values = vega_spec["data"]["values"]

            # Save data as separate JSON file
            data_path = output_path.parent / "data.json"
            with open(data_path, "w", encoding="utf-8") as f:
                json.dump(data_values, f, indent=2, ensure_ascii=False)

        # Create Altair chart from Vega-Lite spec using original embedded data
        # This ensures the chart renders properly during save()
        chart = alt.Chart.from_dict(vega_spec)

        # Save the chart in the specified format
        chart.save(str(output_path))

        # Save the Vega-Lite config as JSON (renamed from spec)
        # Create a config version with relative path for portability
        config_path = output_path.parent / "vega_lite_config.json"
        config_spec = vega_spec.copy()
        if data_path:
            # Replace embedded data with relative path reference in the saved config
            config_spec["data"] = {"url": "./data.json"}
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_spec, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Successfully generated {output_format.upper()} chart: {output_path}"
        )
        logger.info(f"Successfully saved Vega-Lite config: {config_path}")
        if data_path:
            logger.info(f"Successfully saved data: {data_path}")

        # Build response text
        response_text = f"Chart successfully generated and saved to: {output_path.absolute()} ({output_format.upper()} format)\nVega-Lite configuration saved to: {config_path.absolute()}"
        if data_path:
            response_text += f"\nData extracted and saved to: {data_path.absolute()}"

        return [
            TextContent(
                type="text",
                text=response_text,
            )
        ]

    except Exception as e:
        logger.error(f"Error generating chart: {str(e)}")
        return [TextContent(type="text", text=f"Error generating chart: {str(e)}")]


async def handle_list_charts(arguments: dict):
    """Handle list_charts tool calls."""
    try:
        from .tools import get_default_output_dir

        output_dir = get_default_output_dir()
        if not output_dir.exists():
            return [
                TextContent(
                    type="text",
                    text="No charts found. Output directory does not exist.",
                )
            ]

        chart_names = []
        for item in output_dir.iterdir():
            if item.is_dir():
                config_file = item / "vega_lite_config.json"
                if config_file.exists():
                    chart_names.append(item.name)

        if not chart_names:
            return [
                TextContent(type="text", text="No charts found in output directory.")
            ]

        chart_list = "\n".join(f"- {name}" for name in sorted(chart_names))
        return [TextContent(type="text", text=f"Available charts:\n{chart_list}")]

    except Exception as e:
        logger.error(f"Error listing charts: {str(e)}")
        return [TextContent(type="text", text=f"Error listing charts: {str(e)}")]


async def handle_get_chart_config(arguments: dict):
    """Handle get_chart_config tool calls."""
    try:
        chart_name = arguments.get("chart_name")
        if not chart_name:
            return [TextContent(type="text", text="Error: chart_name is required")]

        if not chart_exists(chart_name):
            return [
                TextContent(type="text", text=f"Error: Chart '{chart_name}' not found")
            ]

        chart_dir = get_chart_directory(chart_name)
        config_file = chart_dir / "vega_lite_config.json"

        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        return [TextContent(type="text", text=json.dumps(config, indent=2))]

    except Exception as e:
        logger.error(f"Error getting chart config: {str(e)}")
        return [TextContent(type="text", text=f"Error getting chart config: {str(e)}")]


async def handle_get_chart_data(arguments: dict):
    """Handle get_chart_data tool calls."""
    try:
        chart_name = arguments.get("chart_name")
        if not chart_name:
            return [TextContent(type="text", text="Error: chart_name is required")]

        if not chart_exists(chart_name):
            return [
                TextContent(type="text", text=f"Error: Chart '{chart_name}' not found")
            ]

        chart_dir = get_chart_directory(chart_name)
        data_file = chart_dir / "data.json"

        if not data_file.exists():
            return [
                TextContent(
                    type="text",
                    text=f"Error: No data file found for chart '{chart_name}'",
                )
            ]

        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return [TextContent(type="text", text=json.dumps(data, indent=2))]

    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        return [TextContent(type="text", text=f"Error getting chart data: {str(e)}")]


async def handle_set_chart_config(arguments: dict):
    """Handle set_chart_config tool calls."""
    try:
        chart_name = arguments.get("chart_name")
        config = arguments.get("config")

        if not chart_name:
            return [TextContent(type="text", text="Error: chart_name is required")]
        if not config:
            return [TextContent(type="text", text="Error: config is required")]

        if not chart_exists(chart_name):
            return [
                TextContent(type="text", text=f"Error: Chart '{chart_name}' not found")
            ]

        chart_dir = get_chart_directory(chart_name)
        config_file = chart_dir / "vega_lite_config.json"

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # Regenerate the chart with updated config
        regeneration_result = await regenerate_chart(chart_name)

        logger.info(f"Successfully updated config for chart: {chart_name}")
        response_text = f"Successfully updated configuration for chart '{chart_name}'"
        if regeneration_result:
            response_text += " and regenerated chart"

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error setting chart config: {str(e)}")
        return [TextContent(type="text", text=f"Error setting chart config: {str(e)}")]


async def handle_set_chart_data(arguments: dict):
    """Handle set_chart_data tool calls."""
    try:
        chart_name = arguments.get("chart_name")
        data = arguments.get("data")

        if not chart_name:
            return [TextContent(type="text", text="Error: chart_name is required")]
        if data is None:
            return [TextContent(type="text", text="Error: data is required")]

        if not chart_exists(chart_name):
            return [
                TextContent(type="text", text=f"Error: Chart '{chart_name}' not found")
            ]

        chart_dir = get_chart_directory(chart_name)
        data_file = chart_dir / "data.json"

        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Regenerate the chart with updated data
        regeneration_result = await regenerate_chart(chart_name)

        logger.info(f"Successfully updated data for chart: {chart_name}")
        response_text = f"Successfully updated data for chart '{chart_name}'"
        if regeneration_result:
            response_text += " and regenerated chart"

        return [TextContent(type="text", text=response_text)]

    except Exception as e:
        logger.error(f"Error setting chart data: {str(e)}")
        return [TextContent(type="text", text=f"Error setting chart data: {str(e)}")]


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
    parser.add_argument(
        "--output-format",
        type=str,
        choices=["png", "svg", "pdf"],
        default="svg",
        help="Default output format for charts (default: svg)",
    )
    args = parser.parse_args()

    # Set the output directory and format
    set_default_output_dir(Path(args.output_dir))
    set_default_output_format(args.output_format)
    logger.info(f"Using output directory: {args.output_dir}")
    logger.info(f"Using default output format: {args.output_format}")

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    asyncio.run(run_server())


if __name__ == "__main__":
    main()
