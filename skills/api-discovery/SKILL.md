---
name: api-discovery
description: Finds what APIs, collections, specs, or requests already exist before building something new, and answers questions about how they relate. Use when the user asks "does an API for X already exist," "what depends on this service," "what does this API do," or before scaffolding anything that might already have a Postman equivalent. Covers `postman search`, `postman context-graph`, and `postman context instructions discovery`. Reach for `search` when you know roughly what you're looking for by name; reach for the Context Graph when the question is about relationships, not names.
---

# API Discovery

## Overview

Two unconnected datasets, so pick by data source, not question shape:

- **`search` / `context`** → **Postman-authored artifacts** someone saved
  in Postman (collections, requests, specs, mocks, workspaces). Matches
  text; doesn't reason. "Does something named/shaped like X exist?"
- **`context-graph ask`** → a separately-populated **engineering service
  graph** (built from repo/traffic scanning, not Postman content) —
  natural-language Q&A over discovered services and the dependency edges
  between them. "What depends on billing-api?" — architecture questions
  `search` structurally can't answer, since there's no keyword for a
  dependency edge.

A miss in one says nothing about the other (see Critical Rule 1) — never
fall back to the Context Graph just because a `search` came back empty, or
vice versa.

## `search`

`search <type> <query>` where type is `requests`, `collections`,
`workspaces`, `flows`, `specs`, `mocks`, `environments`, or `documents`.
Default `--ownership organization` only searches inside your org — pass
`external` or `all` before concluding "no API for this exists," since a
partner or public API published outside the org is invisible at the
default scope. `--filter "method=POST AND workspaceId=ws-123"` narrows
further; see [reference/search_filters.md](reference/search_filters.md) for
the full filter field and operator syntax per element type.

## `context-graph`

`context-graph ask "<question>" --wait` is the one to reach for
interactively — it blocks and prints the answer. Without `--wait`, `ask`
returns an id immediately and `status <askId>` checks on it later (exit
code 3 while still running) — useful for a question expected to take a
while, or from a script polling on its own cadence. The query runs against
the team derived from the API key; there's no workspace/team selection.
`--max-steps` caps how much reasoning the service does per question.

The answer is generated, not retrieved verbatim — verify with a re-ask or
narrower query before acting on it for anything consequential (Critical
Rule 3), the same way any AI-generated claim gets checked before it drives
a decision.

## `context instructions discovery`

Postman ships its own prescribed discovery workflow for AI coding agents —
`postman context instructions discovery` prints it. Read this before
building a custom discovery flow out of `search`/`context` primitives; it's
Postman's own recommended sequence (search/context only, no
`context-graph`), not a blank slate to reinvent.

## After discovery: reusing what was found

`dependency add <type> <nameOrId>` formally adds a collection, environment,
or mock found in another workspace as a dependency of the current one —
the step after `search`/`context` finds something worth reusing (e.g.,
feeding `application test`'s contract matching), rather than copying it in
by hand. It takes a Postman entity ID, so it only follows a `search`/
`context` result — a `context-graph` finding names a service, not an ID;
go find that service's collection via `search` first.

## Critical Rules

1. **`context-graph` and `search`/`context` don't share a dataset** (see
   Overview) — check an absence against its own source, never the other
   tool, before reporting it to the user.
2. **An empty default-scope `search` is not proof nothing exists.** Retry
   with `--ownership all` before reporting "no API for this" to the user.
3. **A Context Graph answer is generated reasoning, not a database read.**
   Verify it against a concrete source before treating it as fact,
   especially for anything the user will act on.
4. **`search`, `context-graph`, and `context` are Beta or recently added
   surfaces.** Re-run `-h` before trusting a flag name here if the installed
   CLI is newer than this file assumes — these are the commands most likely
   to have changed since this was written.

## Verification

State which tool actually answered the question (search vs. Context Graph)
and at what `--ownership` scope or with what `--max-steps`/query — a
discovery answer is only as trustworthy as the scope it ran at.

## Reference

- [Search filter syntax](reference/search_filters.md) — filter fields and
  operators per element type, and `--filter-json` shape.
