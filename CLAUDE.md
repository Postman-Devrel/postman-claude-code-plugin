# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

The Postman Plugin for Claude Code — a pure-markdown, configuration-driven plugin that provides full API lifecycle management via the Postman MCP Server. No compiled code, no runtime dependencies, no build step.

## Repository Structure

```
.claude-plugin/plugin.json   # Plugin manifest (name, version, metadata)
.mcp.json                    # MCP server auto-config (Postman MCP at mcp.postman.com)
commands/*.md                # 11 slash commands (/postman:<name>)
skills/*/SKILL.md            # 7 skills (routing, knowledge, agent-ready APIs, CLI, send-request, generate-spec, run-collection)
agents/readiness-analyzer.md # Sub-agent for API readiness analysis
examples/                    # Sample output (readiness report)
assets/                      # GIFs for README
```

## How the Plugin Works

- Claude Code discovers components via `.claude-plugin/plugin.json` manifest
- `.mcp.json` auto-configures the Postman MCP server, providing `mcp__postman__*` tools (111 tools)
- MCP commands use the cloud Postman MCP Server — requires `POSTMAN_API_KEY` environment variable
- CLI commands use the locally installed Postman CLI (`npm install -g postman-cli`) — requires `postman login`
- Plugin is loaded with `claude --plugin-dir /path/to/postman-claude-code-plugin`

## Component Conventions

**Commands** (`commands/*.md`): YAML front matter with `description` and `allowed-tools`. Each defines a structured workflow invoked as `/postman:<name>`.
- MCP commands: setup, sync, codegen, search, test, mock, docs, security
- CLI commands: request, generate-spec, run-collection

**Skills** (`skills/*/SKILL.md`): YAML front matter with `name`, `description`, `user-invocable`. Auto-injected context, not directly invoked. `postman-routing` routes requests to commands; `postman-knowledge` provides MCP tool guidance; `agent-ready-apis` provides readiness criteria; `postman-cli` provides CLI and git sync file structure knowledge.

**Agent** (`agents/readiness-analyzer.md`): YAML front matter with `name`, `description`, `model`, `allowed-tools`. Runs as a sub-agent (sonnet model) for deep API readiness analysis (8 pillars, 48 checks).

## Key MCP Limitations

These are documented in `skills/postman-knowledge/mcp-limitations.md` and must be respected in all commands:

- `searchPostmanElements` searches PUBLIC network only — use `getWorkspaces` + `getCollections` for private content
- `generateCollection` and `syncCollectionWithSpec` return HTTP 202 — must poll for completion
- `syncCollectionWithSpec` supports OpenAPI 3.0 only — use `updateSpecFile` + `generateCollection` for Swagger 2.0 or OpenAPI 3.1
- `createCollection` creates flat collections — nest via `createCollectionFolder` + `createCollectionRequest`
- `createSpec` struggles with specs >50KB — decompose into collection items instead

## Postman CLI Commands

Three commands use the Postman CLI instead of MCP. They require `postman-cli` installed locally (`npm install -g postman-cli`) and authenticated (`postman login`). If CLI is not found, show install instructions and stop.

- `/postman:request` — Send HTTP requests via `postman request <METHOD> <URL>`
- `/postman:generate-spec` — Scan code for API routes, generate OpenAPI 3.0 YAML, validate with `postman spec lint`
- `/postman:run-collection` — Run collection tests via `postman collection run <id>` using cloud IDs from `.postman/resources.yaml`

CLI commands work with Postman's git sync structure: `postman/collections/` (v3 folder format), `postman/environments/`, `postman/specs/`, and `.postman/resources.yaml` for cloud ID mapping.

## Development Notes

- There is no build, lint, or test suite — all "code" is instructional markdown
- Changes are purely editing markdown files with YAML front matter
- When adding a new command, follow the existing front matter pattern in `commands/`
- When adding a new skill, create `skills/<name>/SKILL.md` with proper front matter
- The `allowed-tools` field in front matter controls what tools a command/agent can use
- CLI commands need `Bash` in `allowed-tools`; MCP commands need `mcp__postman__*`
