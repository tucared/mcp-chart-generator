"""
Tool definitions and configurations for the MCP Chart Generator server.
"""

from pathlib import Path
from typing import Optional
from mcp.types import Tool
from pydantic import BaseModel, Field

# Server configuration
DEFAULT_OUTPUT_DIR = Path.cwd() / "tests"


class ChartRequest(BaseModel):
    """Request model for chart generation."""

    vega_lite_spec: dict = Field(
        description="Complete Vega-Lite specification including data"
    )
    output_path: Optional[str] = Field(
        default=None, description="Output file path (defaults to server config)"
    )


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
                },
                "required": ["vega_lite_spec"],
            },
        )
    ]
