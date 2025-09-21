"""
Tool definitions and configurations for the MCP Chart Generator server.
"""

from pathlib import Path
from typing import Optional
from mcp.types import Tool
from pydantic import BaseModel, Field

# Server configuration
DEFAULT_OUTPUT_DIR = Path.cwd() / "tests"
DEFAULT_WIDTH = 400
DEFAULT_HEIGHT = 300


class ChartRequest(BaseModel):
    """Request model for chart generation."""

    vega_lite_spec: dict = Field(
        description="Complete Vega-Lite specification including data"
    )
    output_path: Optional[str] = Field(
        default=None, description="Output file path (defaults to server config)"
    )
    width: Optional[int] = Field(default=None, description="Chart width in pixels")
    height: Optional[int] = Field(default=None, description="Chart height in pixels")


def get_tool_definitions() -> list[Tool]:
    """Get list of available MCP tools."""
    return [
        Tool(
            name="generate_chart",
            description="Generate a PNG chart from a Vega-Lite specification",
            inputSchema={
                "type": "object",
                "properties": {
                    "vega_lite_spec": {
                        "type": "object",
                        "description": "Complete Vega-Lite specification including data",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional output file path (defaults to server config)",
                    },
                    "width": {
                        "type": "integer",
                        "description": "Optional chart width in pixels",
                    },
                    "height": {
                        "type": "integer",
                        "description": "Optional chart height in pixels",
                    },
                },
                "required": ["vega_lite_spec"],
            },
        )
    ]
