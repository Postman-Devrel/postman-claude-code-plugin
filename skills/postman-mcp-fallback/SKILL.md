---
name: postman-mcp-fallback
description: Falls back to Postman's own MCP server when the CLI cannot be used, and is the reference for using that surface once connected. Use when the user explicitly asks to connect an agent to Postman's MCP tools, to pick a toolset, or to judge an MCP result such as a `getCollection` response or a `createMock` default. For agent-initiated routing it is gated to two cases — bootstrap attempted a CLI install and that install actually failed, or the CLI simply has no verb for the task at all (confirmed via `-h`, e.g. adding a comment to a collection) — and a `postman` binary missing from PATH is never on its own a qualifying reason, because bootstrap installs the CLI itself. Covers Postman's API as MCP tools, not the repo-local CLI workflow the other skills drive.
---

# Fall Back to Postman's MCP Server

## Overview

Postman ships its own MCP server — `@postman/postman-mcp-server` — that
exposes the Postman API itself as MCP tools:
create, read, update, and delete workspaces, collections, environments,
specs, mocks, and monitors; run a collection; generate client code; search
the org's API catalog. This is a different integration point from the rest
of this plugin. `bootstrap`, `api-mocking`, `api-testing`, `api-monitoring`,
`spec-authoring`, `performance-testing`, `api-discovery` and `ci-integration`
all wrap the Postman CLI inside a repo's local workflow. This skill governs calling Postman's tools directly once its MCP
server is connected — a different surface, with its own toolset choice, its
own auth model, and defaults that don't match the CLI's.

## Toolsets, chosen at connection time

| Toolset | Size | Contents | Use when |
| --- | --- | --- | --- |
| `minimal` (default) | medium | Core create/read/update on one collection, workspace, environment, spec, or mock at a time; `runCollection`; `duplicateCollection`; `searchPostmanElements` | Modifying a single element, the common case |
| `code` | small, read-only | Context and code-gen tools (`getCodeGenerationInstructions`, `get*Context` family) | Generating client code or feeding API context to the agent, not editing Postman |
| `full` | largest | Everything in `minimal` plus comments, folder/request/response transfer, forks, pull requests, monitors, packages, SDKs, workspace roles, private network management, analytics | The task genuinely needs monitors, SDKs, governance/comments, or Enterprise collaboration |
| `learn` | smallest — one tool | `searchLearningCenter` only | Looking up Postman's own docs, nothing else |

Every extra tool in a toolset costs context on every turn, whether it's
used or not.

Transport is chosen the same way, at connection time, not per call:

- **Remote** (`https://mcp.postman.com/minimal`, `/code`, `/mcp` for full,
  or `/learn`) — OAuth needs no manual key; API-key auth needs an
  `Authorization: Bearer <POSTMAN_API_KEY>` header. Cannot reach `localhost`.
- **Local** (`npx @postman/postman-mcp-server`, STDIO) — needs
  `POSTMAN_API_KEY` set or it exits immediately; add `--code`, `--full`, or
  `--learn` to change toolset. Can reach `localhost` APIs the remote server
  can't.
- **EU residency** — remote at `https://mcp.eu.postman.com/...`, or local
  with `--region eu`. API key only on both; OAuth is US-remote only.

## Critical Rules

1. **This surface is the fallback, not a peer. Reach for it only when the
   CLI genuinely can't do the job, not because installing it was
   inconvenient.** A missing `postman` on `PATH` is not a qualifying
   reason — bootstrap installs the CLI with `npm install -g postman-cli`,
   or a platform installer, and routing here to avoid that install defeats
   the point of the plugin. Two kinds of reason qualify: bootstrap attempted
   an install and it actually failed (no shell, no Node, no write access, or
   a hosted session where the install can't happen), or the CLI simply has
   no verb for the task — confirmed by reading `-h`, not assumed (adding a
   comment to a collection is like this: no CLI verb exists for it, but this
   server's `full` toolset does — monitor create/schedule/run, by contrast,
   is fully covered by the CLI's `monitor` command now, see
   `api-monitoring`). First confirm this surface actually covers
   the gap, from this file's own Overview and toolset table — it doesn't
   cover everything the CLI can't do. Publishing docs externally, for one,
   has no tool here either: that gap routes to a human publishing from the
   Postman app, not to MCP. Once confirmed, say which of the two reasons
   above applies.
2. **Default to `minimal`; only step up when the task needs it.** See the
   table above — don't reach for `full` "to be safe."
3. **Fetch the `postman://instructions` resource before answering anything
   Postman-related — the server asks for this itself, but most MCP hosts
   won't do it automatically.** The server's own `instructions` metadata
   tells the connecting agent to read that resource first. If the host
   doesn't surface it on connect, read it explicitly before the first real
   tool call.
4. **Never conclude "no such API exists" from the visible tool list alone.**
   The tool list is the fixed set of tools for *using* Postman, not a live
   index of every API the organization has published. Before answering
   whether an API exists, call `searchPostmanElements` (`ownership:
   "organization"` by default) — the server's own instructions name this
   exact anti-pattern.
5. **A tool that looks missing may just be off in this toolset — check
   before telling the user to reconfigure.** Call `getEnabledTools`; its own
   description says to run it first when a requested tool is unavailable.
6. **Every mock server this MCP server creates is public unless told
   otherwise.** `createMock`'s `private` parameter defaults to `false` —
   "public and can receive requests from anyone and anywhere." There is no
   local-mock option on this surface at all — that's the CLI, via the
   `api-mocking` skill. Get explicit consent, or pass `private: true`, before
   calling `createMock` or `publishMock`.
7. **`getCollection` returns a lightweight map, not the full collection,
   unless asked.** The default response is metadata plus recursive item
   references. Pass `model: "full"` only when the task actually needs
   request bodies, scripts, or saved examples — the full payload of a large
   collection can be large enough to be worth avoiding by default.

## Process

1. Pick a toolset for the task (table above).
2. Configure the connection — decide remote/local/region using the
   Transport criteria above, then run the matching command:
   - **Remote:** `claude mcp add --transport http postman
     https://mcp.postman.com/minimal` (swap `/code`, `/mcp`, or `/learn`).
   - **Local:** `claude mcp add postman -e POSTMAN_API_KEY=<key> -- npx
     @postman/postman-mcp-server`.
   - **EU residency:** the `mcp.eu.postman.com` URL, or add `--region eu` to
     the local command.
3. Fetch the `postman://instructions` resource, per Critical Rule 3 — do
   this even if the host claims to do it automatically on connect, and
   before the two confirmation calls in step 4.
4. Call `getAuthenticatedUser` to confirm auth, then `getEnabledTools` to
   confirm which toolset actually loaded. State both back to the user
   rather than assuming the configuration took effect.

## Verification

- State which toolset is active, read from `getEnabledTools` — not from
  what was requested in config. State transport and region from the
  connection command that was actually used; `getEnabledTools` doesn't
  report either.
- Before answering "is there an API for X" with "no," confirm
  `searchPostmanElements` actually ran first.
- Before creating or publishing a mock, state explicitly whether it's public
  or `private: true` was passed.
