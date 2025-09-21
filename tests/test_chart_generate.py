#!/usr/bin/env python3
"""
Comprehensive test script to verify chart generation functionality across all formats.
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

import altair as alt

from mcp_chart_generator.server import call_tool
from mcp_chart_generator.tools import (
    ChartRequest,
    get_default_output_format,
    sanitize_chart_title,
    set_default_output_dir,
    set_default_output_format,
)

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


class ChartGenerationTests(unittest.TestCase):
    """Test suite for chart generation functionality."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        set_default_output_dir(self.temp_path)
        set_default_output_format("svg")  # Set default to SVG

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_basic_chart_generation(self):
        """Test basic chart generation functionality."""
        try:
            # Create chart from spec
            chart = alt.Chart.from_dict(sample_spec)

            # Test saving
            test_path = self.temp_path / "test_chart.png"
            chart.save(str(test_path))
            self.assertTrue(test_path.exists())
            print("✅ Basic chart generation test passed!")
        except Exception as e:
            self.fail(f"Basic chart generation test failed: {e}")

    def test_chart_request_validation(self):
        """Test ChartRequest model validation."""
        try:
            # Valid request
            request = ChartRequest(
                chart_title="Test Chart",
                vega_lite_spec=sample_spec,
                output_path="tests/test_output.png",
                output_format="png",
            )
            self.assertEqual(request.chart_title, "Test Chart")
            self.assertEqual(request.output_format, "png")
            print("✅ ChartRequest validation test passed!")
        except Exception as e:
            self.fail(f"ChartRequest validation test failed: {e}")

    def test_output_format_configuration(self):
        """Test output format configuration functions."""
        try:
            # Test default format
            self.assertEqual(get_default_output_format(), "svg")

            # Test setting valid formats
            for format_name in ["png", "svg", "pdf"]:
                set_default_output_format(format_name)
                self.assertEqual(get_default_output_format(), format_name)

            # Test invalid format
            with self.assertRaises(ValueError):
                set_default_output_format("invalid")

            print("✅ Output format configuration test passed!")
        except Exception as e:
            self.fail(f"Output format configuration test failed: {e}")

    def test_chart_title_sanitization(self):
        """Test that chart title sanitization works correctly."""
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
            self.assertEqual(
                result,
                expected,
                f"Expected '{expected}', got '{result}' for input '{input_title}'",
            )

        print("✅ Chart title sanitization test passed!")

    async def test_svg_format_generation(self):
        """Test SVG format chart generation."""
        chart_title = "Test SVG Chart"
        response = await call_tool(
            "generate_chart",
            {
                "chart_title": chart_title,
                "vega_lite_spec": sample_spec,
                "output_format": "svg",
            },
        )

        # Verify response
        self.assertEqual(len(response), 1)
        self.assertIn("SVG format", response[0].text)

        # Verify files exist
        safe_title = sanitize_chart_title(chart_title)
        chart_dir = self.temp_path / safe_title
        svg_file = chart_dir / "graph.svg"
        json_file = chart_dir / "vega_lite_spec.json"

        self.assertTrue(svg_file.exists(), f"SVG file should exist: {svg_file}")
        self.assertTrue(json_file.exists(), f"JSON file should exist: {json_file}")
        self.assertGreater(svg_file.stat().st_size, 0, "SVG file should not be empty")

        print("✅ SVG format generation test passed!")

    async def test_png_format_generation(self):
        """Test PNG format chart generation."""
        chart_title = "Test PNG Chart"
        response = await call_tool(
            "generate_chart",
            {
                "chart_title": chart_title,
                "vega_lite_spec": sample_spec,
                "output_format": "png",
            },
        )

        # Verify response
        self.assertEqual(len(response), 1)
        self.assertIn("PNG format", response[0].text)

        # Verify files exist
        safe_title = sanitize_chart_title(chart_title)
        chart_dir = self.temp_path / safe_title
        png_file = chart_dir / "graph.png"
        json_file = chart_dir / "vega_lite_spec.json"

        self.assertTrue(png_file.exists(), f"PNG file should exist: {png_file}")
        self.assertTrue(json_file.exists(), f"JSON file should exist: {json_file}")
        self.assertGreater(png_file.stat().st_size, 0, "PNG file should not be empty")

        print("✅ PNG format generation test passed!")

    async def test_pdf_format_generation(self):
        """Test PDF format chart generation."""
        chart_title = "Test PDF Chart"
        response = await call_tool(
            "generate_chart",
            {
                "chart_title": chart_title,
                "vega_lite_spec": sample_spec,
                "output_format": "pdf",
            },
        )

        # Verify response
        self.assertEqual(len(response), 1)
        self.assertIn("PDF format", response[0].text)

        # Verify files exist
        safe_title = sanitize_chart_title(chart_title)
        chart_dir = self.temp_path / safe_title
        pdf_file = chart_dir / "graph.pdf"
        json_file = chart_dir / "vega_lite_spec.json"

        self.assertTrue(pdf_file.exists(), f"PDF file should exist: {pdf_file}")
        self.assertTrue(json_file.exists(), f"JSON file should exist: {json_file}")
        self.assertGreater(pdf_file.stat().st_size, 0, "PDF file should not be empty")

        print("✅ PDF format generation test passed!")

    async def test_default_format_behavior(self):
        """Test that default format (SVG) is used when no format specified."""
        chart_title = "Default Format Chart"
        response = await call_tool(
            "generate_chart",
            {
                "chart_title": chart_title,
                "vega_lite_spec": sample_spec,
                # Note: no output_format specified
            },
        )

        # Verify response mentions SVG (the default)
        self.assertEqual(len(response), 1)
        self.assertIn("SVG format", response[0].text)

        # Verify SVG file exists
        safe_title = sanitize_chart_title(chart_title)
        chart_dir = self.temp_path / safe_title
        svg_file = chart_dir / "graph.svg"

        self.assertTrue(svg_file.exists(), f"Default SVG file should exist: {svg_file}")

        print("✅ Default format behavior test passed!")

    async def test_vega_lite_json_content(self):
        """Test that Vega-Lite JSON contains correct content."""
        chart_title = "JSON Content Test"
        await call_tool(
            "generate_chart",
            {
                "chart_title": chart_title,
                "vega_lite_spec": sample_spec,
                "output_format": "svg",
            },
        )

        # Read and verify JSON content
        safe_title = sanitize_chart_title(chart_title)
        chart_dir = self.temp_path / safe_title
        json_file = chart_dir / "vega_lite_spec.json"

        with open(json_file, "r", encoding="utf-8") as f:
            saved_spec = json.load(f)

        # Verify content
        self.assertEqual(saved_spec["title"], chart_title)
        self.assertEqual(saved_spec["mark"], "bar")
        self.assertIn("data", saved_spec)
        self.assertEqual(len(saved_spec["data"]["values"]), 9)

        print("✅ Vega-Lite JSON content test passed!")

    async def test_all_formats_comprehensive(self):
        """Comprehensive test of all formats with file size verification."""
        formats = ["svg", "png", "pdf"]
        file_info = {}

        for format_name in formats:
            chart_title = f"Comprehensive_{format_name.upper()}_Test"
            await call_tool(
                "generate_chart",
                {
                    "chart_title": chart_title,
                    "vega_lite_spec": sample_spec,
                    "output_format": format_name,
                },
            )

            # Check files
            safe_title = sanitize_chart_title(chart_title)
            chart_dir = self.temp_path / safe_title
            chart_file = chart_dir / f"graph.{format_name}"
            json_file = chart_dir / "vega_lite_spec.json"

            self.assertTrue(
                chart_file.exists(), f"{format_name.upper()} file should exist"
            )
            self.assertTrue(
                json_file.exists(), f"JSON file should exist for {format_name}"
            )

            # Store file sizes for comparison
            file_info[format_name] = {
                "chart_size": chart_file.stat().st_size,
                "json_size": json_file.stat().st_size,
            }

        # Verify all formats generated files
        self.assertEqual(len(file_info), 3)

        # SVG should generally be smaller than PNG/PDF for simple charts
        self.assertGreater(file_info["png"]["chart_size"], 0)
        self.assertGreater(file_info["svg"]["chart_size"], 0)
        self.assertGreater(file_info["pdf"]["chart_size"], 0)

        print("✅ Comprehensive all formats test passed!")
        print(f"  SVG: {file_info['svg']['chart_size']} bytes")
        print(f"  PNG: {file_info['png']['chart_size']} bytes")
        print(f"  PDF: {file_info['pdf']['chart_size']} bytes")


async def run_async_tests():
    """Run all async tests."""
    test_instance = ChartGenerationTests()
    test_instance.setUp()

    try:
        await test_instance.test_svg_format_generation()
        await test_instance.test_png_format_generation()
        await test_instance.test_pdf_format_generation()
        await test_instance.test_default_format_behavior()
        await test_instance.test_vega_lite_json_content()
        await test_instance.test_all_formats_comprehensive()
        print("\n🎉 All async tests passed!")
        return True
    except Exception as e:
        print(f"\n❌ Async test failed: {e}")
        return False
    finally:
        test_instance.tearDown()


def run_sync_tests():
    """Run all synchronous tests."""
    try:
        suite = unittest.TestLoader().loadTestsFromTestCase(ChartGenerationTests)
        # Run only sync tests (exclude async methods)
        sync_tests = [
            test
            for test in suite
            if not test._testMethodName.startswith("test_")
            or test._testMethodName
            in [
                "test_basic_chart_generation",
                "test_chart_request_validation",
                "test_output_format_configuration",
                "test_chart_title_sanitization",
            ]
        ]

        if sync_tests:
            runner = unittest.TextTestRunner(verbosity=0)
            result = runner.run(unittest.TestSuite(sync_tests))
            return result.wasSuccessful()
        else:
            # Run sync tests manually
            test_instance = ChartGenerationTests()
            test_instance.setUp()
            try:
                test_instance.test_basic_chart_generation()
                test_instance.test_chart_request_validation()
                test_instance.test_output_format_configuration()
                test_instance.test_chart_title_sanitization()
                print("✅ All sync tests passed!")
                return True
            except Exception as e:
                print(f"❌ Sync test failed: {e}")
                return False
            finally:
                test_instance.tearDown()

    except Exception as e:
        print(f"❌ Error running sync tests: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Running comprehensive chart generation tests...")
    print("=" * 60)

    # Run synchronous tests
    print("\n📋 Running synchronous tests...")
    sync_success = run_sync_tests()

    # Run asynchronous tests
    print("\n🔄 Running asynchronous tests...")
    async_success = asyncio.run(run_async_tests())

    # Summary
    print("\n" + "=" * 60)
    if sync_success and async_success:
        print("🎉 All tests passed! The MCP server supports all formats correctly.")
        print("\nSupported formats:")
        print("  • SVG (default) - Vector format, smallest file size")
        print("  • PNG - Raster format, good for embedding")
        print("  • PDF - Vector format with document structure")
    else:
        print("💥 Some tests failed. Check the implementation.")
        exit(1)
