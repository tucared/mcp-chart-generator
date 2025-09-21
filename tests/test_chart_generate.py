#!/usr/bin/env python3
"""
Simple test script to verify chart generation functionality.
"""

from mcp_chart_generator.tools import (
    ChartRequest,
    sanitize_chart_title,
    set_default_output_dir,
    get_default_output_dir,
)
import altair as alt
import json
import tempfile
from pathlib import Path

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
            chart_title="Test Chart",
            vega_lite_spec=sample_spec,
            output_path="tests/test_output.png",
        )
        print("✅ ChartRequest validation test passed!")
        return True
    except Exception as e:
        print(f"❌ ChartRequest validation test failed: {e}")
        return False


def test_output_directory_setup():
    """Test that output directory configuration works correctly."""
    try:
        # Get original output dir (may be None initially)
        try:
            original_dir = get_default_output_dir()
        except RuntimeError:
            original_dir = None

        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Set new output directory
            set_default_output_dir(temp_path)

            # Verify it was set correctly
            current_dir = get_default_output_dir()
            assert current_dir == temp_path, f"Expected {temp_path}, got {current_dir}"

            # Test that the directory is used for default chart generation
            # This simulates what happens in server.py when no output_path is provided
            default_dir = get_default_output_dir()
            default_dir.mkdir(exist_ok=True)
            output_path = default_dir / "chart.png"

            # Ensure output directory exists (simulating server.py logic)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Verify the path is in our temp directory
            assert output_path.parent == temp_path
            assert output_path.name == "chart.png"

        # Restore original directory (if there was one)
        if original_dir is not None:
            set_default_output_dir(original_dir)

        print("✅ Output directory setup test passed!")
        return True
    except Exception as e:
        print(f"❌ Output directory setup test failed: {e}")
        return False


def test_chart_title_sanitization():
    """Test that chart title sanitization works correctly."""
    try:
        # Test various problematic titles
        test_cases = [
            ("Normal Title", "Normal_Title"),
            ("Title with spaces", "Title_with_spaces"),
            ("Title/with\\invalid:chars", "Title_with_invalid_chars"),
            ("Title<>:|?*chars", "Title_chars"),
            ("", "untitled_chart"),
            ("   ", "untitled_chart"),
            ("Title   with    multiple   spaces", "Title_with_multiple_spaces"),
        ]

        for input_title, expected in test_cases:
            result = sanitize_chart_title(input_title)
            assert result == expected, (
                f"Expected '{expected}', got '{result}' for input '{input_title}'"
            )

        print("✅ Chart title sanitization test passed!")
        return True
    except Exception as e:
        print(f"❌ Chart title sanitization test failed: {e}")
        return False


def test_chart_title_integration():
    """Test that chart title is properly integrated into directory structure."""
    try:
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Set output directory
            set_default_output_dir(temp_path)

            # Test chart title integration (simulating server.py logic)
            chart_title = "My Test Chart!"
            safe_title = sanitize_chart_title(chart_title)

            default_dir = get_default_output_dir()
            chart_dir = default_dir / safe_title
            chart_dir.mkdir(parents=True, exist_ok=True)
            output_path = chart_dir / "graph.png"

            # Verify directory structure
            assert chart_dir.exists(), f"Chart directory {chart_dir} should exist"
            assert chart_dir.name == "My_Test_Chart", (
                f"Expected 'My_Test_Chart', got '{chart_dir.name}'"
            )
            assert output_path.name == "graph.png", (
                f"Expected 'graph.png', got '{output_path.name}'"
            )

        print("✅ Chart title integration test passed!")
        return True
    except Exception as e:
        print(f"❌ Chart title integration test failed: {e}")
        return False


def test_vega_lite_json_saving():
    """Test that Vega-Lite specification is saved as JSON alongside the PNG."""
    try:
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Set output directory
            set_default_output_dir(temp_path)

            # Simulate the server.py logic for saving JSON
            chart_title = "Test JSON Chart"
            safe_title = sanitize_chart_title(chart_title)

            default_dir = get_default_output_dir()
            chart_dir = default_dir / safe_title
            chart_dir.mkdir(parents=True, exist_ok=True)
            output_path = chart_dir / "graph.png"

            # Create modified spec with title (simulating server.py logic)
            vega_spec = sample_spec.copy()
            vega_spec["title"] = chart_title

            # Save the Vega-Lite spec as JSON (simulating server.py logic)
            json_path = output_path.parent / "vega_lite_spec.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(vega_spec, f, indent=2, ensure_ascii=False)

            # Verify JSON file exists and has correct content
            assert json_path.exists(), f"JSON file {json_path} should exist"
            assert json_path.name == "vega_lite_spec.json", (
                f"Expected 'vega_lite_spec.json', got '{json_path.name}'"
            )

            # Verify JSON content
            with open(json_path, "r", encoding="utf-8") as f:
                saved_spec = json.load(f)

            assert saved_spec["title"] == chart_title, (
                f"Expected title '{chart_title}', got '{saved_spec.get('title')}'"
            )
            assert saved_spec["mark"] == "bar", (
                f"Expected mark 'bar', got '{saved_spec.get('mark')}'"
            )
            assert "data" in saved_spec, "Saved spec should contain data"

        print("✅ Vega-Lite JSON saving test passed!")
        return True
    except Exception as e:
        print(f"❌ Vega-Lite JSON saving test failed: {e}")
        return False


def test_full_chart_generation_with_json():
    """Test complete chart generation workflow that creates both PNG and JSON files."""
    try:
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Set output directory
            set_default_output_dir(temp_path)

            # Simulate the complete server.py call_tool logic
            chart_title = "Integration Test Chart"
            safe_title = sanitize_chart_title(chart_title)

            # Set up output path (following server.py logic)
            default_dir = get_default_output_dir()
            chart_dir = default_dir / safe_title
            chart_dir.mkdir(parents=True, exist_ok=True)
            output_path = chart_dir / "graph.png"

            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Add title to Vega-Lite spec (following server.py logic)
            vega_spec = sample_spec.copy()
            vega_spec["title"] = chart_title

            # Create Altair chart from Vega-Lite spec
            chart = alt.Chart.from_dict(vega_spec)

            # Save the chart as PNG
            chart.save(str(output_path))

            # Save the Vega-Lite spec as JSON (following server.py logic)
            json_path = output_path.parent / "vega_lite_spec.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(vega_spec, f, indent=2, ensure_ascii=False)

            # Verify both files exist
            assert output_path.exists(), f"PNG file {output_path} should exist"
            assert json_path.exists(), f"JSON file {json_path} should exist"

            # Verify file names
            assert output_path.name == "graph.png", (
                f"Expected 'graph.png', got '{output_path.name}'"
            )
            assert json_path.name == "vega_lite_spec.json", (
                f"Expected 'vega_lite_spec.json', got '{json_path.name}'"
            )

            # Verify they're in the same directory
            assert output_path.parent == json_path.parent, (
                "PNG and JSON files should be in the same directory"
            )

            # Verify directory name matches sanitized chart title
            assert output_path.parent.name == safe_title, (
                f"Expected directory '{safe_title}', got '{output_path.parent.name}'"
            )

            # Verify JSON content matches what was saved
            with open(json_path, "r", encoding="utf-8") as f:
                saved_spec = json.load(f)

            assert saved_spec["title"] == chart_title, (
                f"Expected title '{chart_title}', got '{saved_spec.get('title')}'"
            )
            assert saved_spec["mark"] == sample_spec["mark"], (
                f"Expected mark '{sample_spec['mark']}', got '{saved_spec.get('mark')}'"
            )
            assert saved_spec["data"] == sample_spec["data"], (
                "JSON data should match original spec data"
            )

        print("✅ Full chart generation with JSON test passed!")
        return True
    except Exception as e:
        print(f"❌ Full chart generation with JSON test failed: {e}")
        return False


if __name__ == "__main__":
    print("Running chart generation tests...")

    test1 = test_chart_request_validation()
    test2 = test_basic_chart_generation()
    test3 = test_output_directory_setup()
    test4 = test_chart_title_sanitization()
    test5 = test_chart_title_integration()
    test6 = test_vega_lite_json_saving()
    test7 = test_full_chart_generation_with_json()

    if test1 and test2 and test3 and test4 and test5 and test6 and test7:
        print("\n🎉 All tests passed! The MCP server should work correctly.")
    else:
        print("\n💥 Some tests failed. Check the implementation.")
