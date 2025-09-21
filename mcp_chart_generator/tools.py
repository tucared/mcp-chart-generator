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


def set_default_output_dir(output_dir: Path) -> None:
    """Set the default output directory for chart generation."""
    global _DEFAULT_OUTPUT_DIR
    _DEFAULT_OUTPUT_DIR = output_dir


def get_default_output_dir() -> Path:
    """Get the current default output directory."""
    if _DEFAULT_OUTPUT_DIR is None:
        raise RuntimeError(
            "Default output directory not set. Server must be started with --output-dir parameter."
        )
    return _DEFAULT_OUTPUT_DIR


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
            name="generate_chart",
            description="Generate a PNG chart from a Vega-Lite specification",
            inputSchema={
                "type": "object",
                "properties": {
                    "chart_title": {
                        "type": "string",
                        "description": "Title for the chart, used as directory name and chart title",
                    },
                    "vega_lite_spec": {
                        "type": "object",
                        "description": "Complete Vega-Lite specification including data",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path (defaults to server config)",
                    },
                },
                "required": ["chart_title", "vega_lite_spec"],
            },
        )
    ]
