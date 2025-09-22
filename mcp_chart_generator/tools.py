"""
Tool definitions and configurations for the MCP Chart Generator server.
"""

import re
from pathlib import Path
from typing import Optional
from mcp.types import Tool
from pydantic import BaseModel, Field

# Server configuration - must be set via set_default_output_dir()
_DEFAULT_OUTPUT_DIR = None
_DEFAULT_OUTPUT_FORMAT = "svg"


class ChartRequest(BaseModel):
    """Request model for chart generation."""

    chart_title: str = Field(
        description="Title for the chart, used as directory name and chart title"
    )
    vega_lite_spec: dict = Field(
        description="Complete Vega-Lite specification including data"
    )
    output_path: Optional[str] = Field(
        default=None, description="Output file path (defaults to server config)"
    )
    output_format: Optional[str] = Field(
        default=None,
        description="Output format: 'png', 'svg', or 'pdf' (defaults to server config)",
    )


def set_default_output_dir(output_dir: Path) -> None:
    """Set the default output directory for chart generation."""
    global _DEFAULT_OUTPUT_DIR
    _DEFAULT_OUTPUT_DIR = output_dir


def set_default_output_format(output_format: str) -> None:
    """Set the default output format for chart generation."""
    global _DEFAULT_OUTPUT_FORMAT
    if output_format.lower() not in ["png", "svg", "pdf"]:
        raise ValueError(
            f"Invalid output format: {output_format}. Must be 'png', 'svg', or 'pdf'."
        )
    _DEFAULT_OUTPUT_FORMAT = output_format.lower()


def get_default_output_dir() -> Path:
    """Get the current default output directory."""
    if _DEFAULT_OUTPUT_DIR is None:
        raise RuntimeError(
            "Default output directory not set. Server must be started with --output-dir parameter."
        )
    return _DEFAULT_OUTPUT_DIR


def get_default_output_format() -> str:
    """Get the current default output format."""
    return _DEFAULT_OUTPUT_FORMAT


def get_chart_directory(chart_name: str) -> Path:
    """Get the directory path for a chart by name."""
    sanitized_name = sanitize_chart_title(chart_name)
    return get_default_output_dir() / sanitized_name


def chart_exists(chart_name: str) -> bool:
    """Check if a chart exists by verifying its directory and config file."""
    chart_dir = get_chart_directory(chart_name)
    config_file = chart_dir / "vega_lite_config.json"
    return chart_dir.exists() and config_file.exists()


def sanitize_chart_title(title: str) -> str:
    """Sanitize chart title for use as a directory name."""
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", title)
    # Remove or replace other problematic characters
    sanitized = re.sub(r"[^\w\s-]", "", sanitized)
    # Replace spaces with underscores and collapse multiple underscores
    sanitized = re.sub(r"[\s_]+", "_", sanitized)
    # Remove leading/trailing underscores and limit length
    sanitized = sanitized.strip("_")[:100]
    # Ensure it's not empty
    return sanitized if sanitized else "untitled_chart"


def get_tool_definitions() -> list[Tool]:
    """Get list of available MCP tools."""
    return [
        Tool(
            name="create_chart",
            description="Create charts from a Vega-Lite specification in PNG, SVG, or PDF format. Automatically separates embedded data into data.json and creates vega_lite_config.json for better token efficiency.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_title": {
                        "type": "string",
                        "description": "Title for the chart, used as directory name and chart title",
                    },
                    "vega_lite_spec": {
                        "type": "object",
                        "description": "Complete Vega-Lite specification including data. If data.values is present, it will be extracted to data.json and replaced with data.url reference.",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path (defaults to server config)",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["png", "svg", "pdf"],
                        "description": "Output format: 'png', 'svg', or 'pdf' (defaults to server config, currently 'svg')",
                    },
                },
                "required": ["chart_title", "vega_lite_spec"],
            },
        ),
        Tool(
            name="list_charts",
            description="List all available charts in the output directory.",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        Tool(
            name="get_chart_config",
            description="Get the Vega-Lite configuration for a specific chart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_name": {
                        "type": "string",
                        "description": "Name of the chart to retrieve configuration for",
                    },
                },
                "required": ["chart_name"],
            },
        ),
        Tool(
            name="get_chart_data",
            description="Get the data for a specific chart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_name": {
                        "type": "string",
                        "description": "Name of the chart to retrieve data for",
                    },
                },
                "required": ["chart_name"],
            },
        ),
        Tool(
            name="set_chart_config",
            description="Update the Vega-Lite configuration for a specific chart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_name": {
                        "type": "string",
                        "description": "Name of the chart to update configuration for",
                    },
                    "config": {
                        "type": "object",
                        "description": "New Vega-Lite configuration object",
                    },
                },
                "required": ["chart_name", "config"],
            },
        ),
        Tool(
            name="set_chart_data",
            description="Update the data for a specific chart.",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_name": {
                        "type": "string",
                        "description": "Name of the chart to update data for",
                    },
                    "data": {
                        "type": "array",
                        "description": "New data array for the chart",
                    },
                },
                "required": ["chart_name", "data"],
            },
        ),
    ]
