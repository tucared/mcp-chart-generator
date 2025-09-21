# mcp-chart-generator

This repository contains the code for a MCP server that allow clients (eg. Claude Code) to
generate charts that are saved to file artefacts for versionning and auditing capabilites.

This MCP server is built in Python using Vega-Altair library, so it can use Vega-Lite syntax.

A single tool call creates a folder where are saved : Input data, Vega-Lite specification and output chart.

## Editing the server

Install pre-commits

```shell
uv run pre-commit install
```

## Acknowledgment

I wanna give a shout to [Issac Wasserman](https://github.com/isaacwasserman) who created a very similar MCP ([mcp-vegalite-server](https://github.com/isaacwasserman/mcp-vegalite-server/tree/main))
where essentially graphs are non persistent, where the present implementation focuses
on making implementation persist as artefacts in the repo.
