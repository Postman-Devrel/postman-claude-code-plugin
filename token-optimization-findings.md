# Token Optimization Findings — Postman Plugin for Claude Code

This document summarizes a token-usage review and optimization pass on the Postman Plugin for Claude Code. The plugin is pure instructional markdown, so its entire "runtime cost" is the context-window tokens it consumes in users' Claude Code sessions. Every token the plugin injects is a token the user can't spend on their actual work — and a token they pay for.

## Where a plugin's tokens actually go

A Claude Code plugin spends tokens in three distinct ways, and they are not equally expensive:

1. **Always-on cost** — every skill, command, and agent `description` from the YAML front matter is injected into *every session's* system prompt, whether or not the user touches Postman. This is the most expensive token in the plugin: it's paid by every user, every session.
2. **Per-trigger cost** — when Claude decides a skill is relevant, the *entire* SKILL.md body loads into context. A 19KB skill costs ~4,800 tokens every time it fires, even if the user only needed a third of it.
3. **Runtime cost** — tool output, async polling loops, and verbose intermediate narration during command execution.

There's also a fourth, plugin-adjacent cost: the **MCP server's tool schemas**. The Postman MCP Server's full mode exposes 100+ tools. On clients that eagerly load schemas that's roughly 40–70k tokens before the user types anything. Recent Claude Code versions defer MCP tool loading (schemas load on demand via tool search), which largely neutralizes this — but it shaped one decision below.

## Why we did NOT switch to the smaller MCP server

The obvious-looking fix — pointing `.mcp.json` at Postman's minimal MCP endpoint (42 tools instead of 100+) — turned out to be wrong. Reading the server's source (`enabledResources.ts` in `postmanlabs/postman-mcp-server`) showed minimal mode is missing:

- All nine `*Context` tools (`getRequestCodeContext`, `getCollectionContext`, …) — which would silently break the plugin's flagship client-code-generation skill
- The async task polling tools (`getAsyncSpecTaskStatus`, `getStatusOfAnAsyncApiTask`) — breaking the HTTP 202 polling workflow that `sync` and `mock` depend on
- `createCollectionFolder` — the documented workaround for nesting flat collections
- `publishDocumentation` and the mock-server-response tools

**Lesson:** measure functionality loss before chasing schema savings. Instead, the URL is now `https://mcp.postman.com/${POSTMAN_MCP_MODE:-mcp}` — full mode by default (safe because modern Claude Code defers schema loading), with an opt-in escape hatch (`minimal` or `code`) for users on older clients who don't need every workflow.

## Changes made

### 1. Progressive disclosure for the two largest skills

The biggest per-trigger win. A skill doesn't need to front-load every rule it might ever apply — it needs the workflow, plus pointers to detailed rules that Claude reads with the Read tool *only at the step that needs them*. The plugin already used this pattern in one place (`agent-ready-apis` + `pillars.md`); it's now applied consistently:

| Skill | Before | After (SKILL.md) | Moved to on-demand references |
|---|---|---|---|
| `postman-context` | 19.0KB (~4,760 tokens) | 7.7KB (~1,930 tokens) | `references/code-generation.md` (7.8KB), `references/maintenance.md` (2.1KB) |
| `generate-spec` | 10.6KB (~2,640 tokens) | 7.2KB (~1,800 tokens) | `references/spec-template.md` (2.9KB) |

No content was deleted — the code-generation rules, maintenance rules, and OpenAPI template are intact, just deferred. A user who asks "find me an email API" no longer pays ~2,800 tokens for code-generation rules they aren't using; a user who does generate code pays the same total as before.

**Savings: ~2,800 tokens per `postman-context` trigger and ~840 tokens per `generate-spec` trigger, in the common cases that don't need the reference material.**

### 2. Removed the manual routing skill entirely

The plugin shipped a `postman-routing` skill (3.3KB, ~835 tokens) whose trigger was "use when user mentions APIs" — broad enough to fire in nearly any backend coding session, Postman-related or not. Its body was a routing table that restated what every command's `description` already tells Claude.

Modern Claude Code routes natively: it matches user intent against component descriptions. A hand-maintained routing table is duplicate state — extra tokens *and* a second place to update on every change. The skill is deleted; each component's description now carries its own routing signal.

**Savings: ~835 tokens in every session where it fired (which, given the trigger, was most sessions in API codebases), plus its share of the always-on description block.**

### 3. Tightened always-on front-matter descriptions

Several descriptions enumerated long quoted trigger-phrase lists ("use when user says 'run tests', 'run collection', 'run my postman tests', …"). These were rewritten as one or two sentences stating capability + when to use, which is what Claude's router actually needs. Combined with the routing-skill removal, the always-on description block went from 3,182 to 2,562 bytes.

**Savings: ~155 tokens in *every* session of *every* plugin user — the highest-leverage bytes in the repo.**

### 4. Scoped `allowed-tools` from wildcard to explicit tool lists

Every MCP command and the readiness-analyzer agent previously declared `allowed-tools: mcp__postman__*` (all 100+ tools). Each now lists exactly the tools its workflow calls — e.g. `setup` declares 6 tools, the readiness-analyzer 11 instead of 111.

This is primarily a precision and least-privilege win, but it has real token effects: sub-agents and clients that resolve tool schemas from the allowlist load an order of magnitude fewer schemas, and a scoped list prevents the model from wandering into unrelated tools mid-command. The audit also surfaced three latent bugs: `docs` could be asked to write a markdown file without `Write` permission, and `security` and the readiness-analyzer were instructed to "apply fixes" without `Edit`/`Write`. Fixed.

### 5. Cheaper async polling

`generateCollection` and `syncCollectionWithSpec` return HTTP 202 and require polling. The `sync`, `mock`, and `docs` commands now instruct: poll with increasing waits (2s → 4s → 8s) and report only the final outcome instead of narrating every poll. Fewer tool round-trips, less intermediate output in context.

### 6. Repo and docs cleanup

- Removed the four README GIFs (out of date after these changes; they also bloated clone size, though they never cost context tokens)
- Rewrote the README: OAuth-first Quick Start, "Auto-Routing" section replaced with "Natural Language Routing" (native), documented `POSTMAN_MCP_MODE`
- Updated CLAUDE.md so future contributors keep the conventions: descriptions stay short, bulky skill content goes in `references/`, `allowed-tools` lists explicit tool names

## Estimated impact

Using the ~4 characters/token rule of thumb:

| Change | Who pays today | Saving |
|---|---|---|
| Routing skill removed | Nearly every session in an API codebase | ~835 tokens/session |
| Description trims | Every session, every user | ~155 tokens/session |
| `postman-context` split | Every session that triggers the skill | up to ~2,800 tokens/trigger |
| `generate-spec` split | Every session that triggers the skill | up to ~840 tokens/trigger |
| Scoped `allowed-tools` | Sub-agent spawns; older/eager clients | up to ~10s of thousands of tokens on eager-loading clients; precision win elsewhere |
| `POSTMAN_MCP_MODE` opt-in | Users on older clients who opt in | ~40–70k tokens/session (minimal/code vs full, eager loading) |
| Polling + drill-down guidance | Long-running sync/mock/docs runs | variable; fewer round-trips and less narration |

A typical "explore an API and generate a client" session that previously loaded the routing skill plus the full `postman-context` skill saves roughly **3,600 tokens** before any work happens; a session that never touches Postman saves ~990 tokens it used to spend on routing overhead.

## Takeaways for plugin authors

1. **Treat front-matter descriptions as the most expensive real estate you own.** They're injected into every session. One or two sentences: what it does, when to use it.
2. **Progressive disclosure beats monolithic skills.** Keep SKILL.md to the workflow (~6KB or less); move templates, rule catalogs, and edge-case handling to `references/*.md` that the skill reads on demand.
3. **Don't build what the harness already does.** A routing skill duplicating Claude's native description-based routing costs tokens twice and creates a maintenance hazard.
4. **Verify before downsizing an MCP server.** Smaller tool modes can silently drop the exact tools your workflows depend on — read the server's tool manifest, don't guess.
5. **Scope `allowed-tools` to what each component calls.** It's least-privilege hygiene, it loads fewer schemas where that matters, and the audit itself tends to find permission bugs.
6. **Make polling cheap.** Any 202-style async workflow should specify backoff and final-result-only reporting, or the model will happily narrate every poll.
