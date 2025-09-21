# mcp-chart-generator

This repository contains the code for a MCP server that allow clients (eg. Claude Code) to
generate charts that are saved to file artefacts for versionning and auditing capabilites.

This MCP server is built in Python using Vega-Altair library, so it can use Vega-Lite syntax.

A single tool call creates a folder where are saved : Input data, Vega-Lite specification and output chart.
