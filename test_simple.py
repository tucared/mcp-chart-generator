#!/usr/bin/env python3
"""
Simple test that actually calls the MCP server function and creates real files.
Run this to see both PNG and JSON files generated in the test_output folder.
"""

import asyncio
import sys
from pathlib import Path

# Add the package to the path so we can import it
sys.path.insert(0, str(Path(__file__).parent))

from mcp_chart_generator.server import call_tool
from mcp_chart_generator.tools import set_default_output_dir

# Sample Vega-Lite specification
sample_spec = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "A simple bar chart with embedded data.",
    "data": {
        "values": [
            {"a": "A", "b": 28},
            {"a": "B", "b": 55},
            {"a": "C", "b": 43},
            {"a": "D", "b": 91},
            {"a": "E", "b": 81},
            {"a": "F", "b": 53},
            {"a": "G", "b": 19},
            {"a": "H", "b": 87},
            {"a": "I", "b": 52},
        ]
    },
    "mark": "bar",
    "encoding": {
        "x": {"field": "a", "type": "nominal", "axis": {"labelAngle": 0}},
        "y": {"field": "b", "type": "quantitative"},
    },
}


async def test_mcp_chart_generation():
    """Test the actual MCP server function and create real files."""

    # Create test output directory
    test_output_dir = Path(__file__).parent / "tests" / "output"
    test_output_dir.mkdir(exist_ok=True)

    # Set the default output directory
    set_default_output_dir(test_output_dir)

    print(f"Testing chart generation in: {test_output_dir.absolute()}")

    # Call the actual MCP server function
    result = await call_tool(
        name="generate_chart",
        arguments={"chart_title": "Simple Test Chart", "vega_lite_spec": sample_spec},
    )

    print("Server response:")
    for content in result:
        print(f"  {content.text}")

    # Check what files were created
    chart_dir = test_output_dir / "Simple_Test_Chart"
    png_file = chart_dir / "graph.png"
    json_file = chart_dir / "vega_lite_spec.json"

    print(f"\nFiles in {chart_dir}:")
    if chart_dir.exists():
        for file in chart_dir.iterdir():
            print(f"  ✅ {file.name} ({file.stat().st_size} bytes)")
    else:
        print("  ❌ Chart directory does not exist")
        return False

    # Verify both files exist
    if png_file.exists() and json_file.exists():
        print("\n🎉 Success! Both files created:")
        print(f"  📊 PNG: {png_file}")
        print(f"  📝 JSON: {json_file}")

        # Show JSON content
        import json

        with open(json_file, "r") as f:
            json_content = json.load(f)
        print("\nJSON content preview:")
        print(f"  Title: {json_content.get('title')}")
        print(f"  Mark: {json_content.get('mark')}")
        print(f"  Data points: {len(json_content.get('data', {}).get('values', []))}")

        return True
    else:
        print("\n❌ Missing files:")
        print(f"  PNG exists: {png_file.exists()}")
        print(f"  JSON exists: {json_file.exists()}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_mcp_chart_generation())
    if success:
        print("\n✅ Test passed! Check the tests/output folder for your files.")
    else:
        print("\n❌ Test failed!")
