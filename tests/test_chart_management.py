#!/usr/bin/env python3
"""
Test for chart management functionality.
"""

import asyncio
import tempfile
import unittest
from pathlib import Path

from mcp_chart_generator.server import call_tool
from mcp_chart_generator.tools import set_default_output_dir

# Sample Vega-Lite specification
SAMPLE_SPEC = {
    "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
    "description": "A simple bar chart with embedded data.",
    "data": {
        "values": [
            {"a": "A", "b": 28},
            {"a": "B", "b": 55},
            {"a": "C", "b": 43},
        ]
    },
    "mark": "bar",
    "encoding": {
        "x": {"field": "a", "type": "nominal"},
        "y": {"field": "b", "type": "quantitative"},
    },
}


class TestChartManagement(unittest.TestCase):
    """Test chart management functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        set_default_output_dir(self.temp_path)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    async def test_chart_management_workflow(self):
        """Test the complete chart management workflow."""
        # 1. Test list_charts with empty directory
        response = await call_tool("list_charts", {})
        self.assertIn("No charts found", response[0].text)

        # 2. Create a test chart
        response = await call_tool(
            "create_chart",
            {
                "chart_title": "Test Management Chart",
                "vega_lite_spec": SAMPLE_SPEC,
            },
        )
        self.assertIn("successfully generated", response[0].text)

        # 3. Test list_charts with chart present
        response = await call_tool("list_charts", {})
        self.assertIn("Test_Management_Chart", response[0].text)

        # 4. Test get_chart_config
        response = await call_tool(
            "get_chart_config", {"chart_name": "Test Management Chart"}
        )
        self.assertIn('"mark": "bar"', response[0].text)

        # 5. Test get_chart_data
        response = await call_tool(
            "get_chart_data", {"chart_name": "Test Management Chart"}
        )
        self.assertIn('"a": "A"', response[0].text)

        # 6. Test set_chart_config
        new_config = SAMPLE_SPEC.copy()
        new_config["title"] = "Updated Chart Title"
        response = await call_tool(
            "set_chart_config",
            {"chart_name": "Test Management Chart", "config": new_config},
        )
        self.assertIn("Successfully updated configuration", response[0].text)

        # 7. Test set_chart_data
        new_data = [
            {"a": "X", "b": 100},
            {"a": "Y", "b": 200},
        ]
        response = await call_tool(
            "set_chart_data", {"chart_name": "Test Management Chart", "data": new_data}
        )
        self.assertIn("Successfully updated data", response[0].text)

        # 8. Verify the updates
        response = await call_tool(
            "get_chart_config", {"chart_name": "Test Management Chart"}
        )
        self.assertIn("Updated Chart Title", response[0].text)

        response = await call_tool(
            "get_chart_data", {"chart_name": "Test Management Chart"}
        )
        self.assertIn('"a": "X"', response[0].text)

    async def test_error_handling(self):
        """Test error handling for non-existent charts."""
        # Test get_chart_config with non-existent chart
        response = await call_tool(
            "get_chart_config", {"chart_name": "Non Existent Chart"}
        )
        self.assertIn("not found", response[0].text)

        # Test get_chart_data with non-existent chart
        response = await call_tool(
            "get_chart_data", {"chart_name": "Non Existent Chart"}
        )
        self.assertIn("not found", response[0].text)

        # Test set_chart_config with non-existent chart
        response = await call_tool(
            "set_chart_config",
            {"chart_name": "Non Existent Chart", "config": {"mark": "bar"}},
        )
        self.assertIn("not found", response[0].text)

        # Test set_chart_data with non-existent chart
        response = await call_tool(
            "set_chart_data",
            {"chart_name": "Non Existent Chart", "data": [{"a": 1}]},
        )
        self.assertIn("not found", response[0].text)


async def run_management_tests():
    """Run chart management tests."""
    test_instance = TestChartManagement()
    test_instance.setUp()

    try:
        await test_instance.test_chart_management_workflow()
        await test_instance.test_error_handling()
        print("🎉 Chart management tests completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Management tests failed: {e}")
        return False
    finally:
        test_instance.tearDown()


if __name__ == "__main__":
    print("🚀 Running chart management tests...")
    success = asyncio.run(run_management_tests())

    if success:
        print("✅ All management tests passed!")
    else:
        print("💥 Management tests failed!")
        exit(1)
