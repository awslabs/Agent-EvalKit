# AGENTS.md

## Project

Agent-EvalKit — a CLI toolkit that automates evaluation of AI agents. Installed via `uv tool install evalkit`. Python 3.11+, built with Hatch.

## Structure

- `src/evalkit/__init__.py` — single-file CLI app (Typer + Rich). Entry point: `evalkit:main`. Handles `init` and `check` subcommands.
- `commands/` — markdown-based slash command definitions (`/evalkit.plan`, `/evalkit.data`, etc.) used by coding assistants (Claude Code, Kilo Code, Kiro CLI).
- `templates/` — evaluation plan and report markdown templates.
- `scripts/bash/` — shell scripts invoked by commands.
- `tracing/` — OpenTelemetry collector setup and trace processing.
- `reference/` — reference docs for deepeval and strands libraries.
- `examples/qa_agent_evaluation/` — complete example evaluation workflow.
- `mcps/` — MCP server configuration.

## Build & Install

```bash
uv tool install evalkit --from .          # local install
uv run evalkit check                      # verify prerequisites
```

## Release

CI in `.github/workflows/release.yml`. Versioning uses sorted git tags (see recent commit `4428c92`).

## Conventions

- Single source file for the CLI — keep `src/evalkit/__init__.py` as the sole Python module.
- Slash commands are defined as markdown files in `commands/` with YAML frontmatter.
- Use `uv` for all Python tooling (not pip/poetry).
