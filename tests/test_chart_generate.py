#!/usr/bin/env python3
"""
Simple test script to verify chart generation functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools import ChartRequest
import altair as alt

# Sample Vega-Lite specification with embedded data
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


def test_basic_chart_generation():
    """Test basic chart generation functionality."""
    try:
        # Create chart from spec
        chart = alt.Chart.from_dict(sample_spec)

        # Test saving
        chart.save("tests/test_chart.png")
        print("✅ Basic chart generation test passed!")
        return True
    except Exception as e:
        print(f"❌ Basic chart generation test failed: {e}")
        return False


def test_chart_request_validation():
    """Test ChartRequest model validation."""
    try:
        # Valid request
        ChartRequest(
            vega_lite_spec=sample_spec,
            output_path="tests/test_output.png",
            width=500,
            height=400,
        )
        print("✅ ChartRequest validation test passed!")
        return True
    except Exception as e:
        print(f"❌ ChartRequest validation test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running chart generation tests...")

    test1 = test_chart_request_validation()
    test2 = test_basic_chart_generation()

    if test1 and test2:
        print("\n🎉 All tests passed! The MCP server should work correctly.")
    else:
        print("\n💥 Some tests failed. Check the implementation.")
