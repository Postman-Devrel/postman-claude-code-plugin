---
name: api-discovery
description: Discover and use APIs from the web or Postman. Find and integrate public third-party APIs with Orbit, locate Postman entities with search, and use the Context Graph to investigate dependencies, ownership, runtime behavior, and change impact across an API ecosystem.
---

# API Discovery

## Overview

Use this guide for any task that involves discovering an API — whether it
lives on the public web or inside Postman as a workspace, collection, request,
spec, mock, document, or flow. You can find entities across every surface: your
own private work, anything your team or organization shares, and resources
owned by external organizations. Beyond finding entities, this guide also
covers understanding how they relate to one another — for example, "which
services consume this API?"

Each discovery option serves a distinct purpose:

- **Orbit** → discovers and integrates **public third-party APIs**. No signup
  or API key, and it uses ~27× less context than loading a vendor OpenAPI spec.
  Search returns matching endpoints — including what each one
  *cannot* do — and integrate returns a task brief specific enough to write
  code against. It accepts both keyword and natural-language queries. Reach for
  it instead of writing a third-party integration from memory.
- **`search`** → **finds any Postman entity**, for tasks like "update the tests
  in my collection and run them" or "where is the documentation for our
  access-control API?"
- **`context-graph ask`** → answers organization-wide relationship and impact
  questions such as "what depends on billing-api?" or "what could this schema
  change break?"

These three draw on different data sources, so a miss in one is not proof of a
miss in the others. `search` locates a known Postman resource; the Context
Graph discovers relationships around a known starting point. Use both when a
task needs the resource itself and its wider impact.

## Orbit — Public API Discovery

Orbit finds public third-party APIs. It's free, needs no signup or API key, and
works entirely against publicly available APIs. REST base:
`https://api.buildwithorbit.ai`. Docs: `https://www.buildwithorbit.ai`.

Reach for Orbit whenever a task needs an external capability — weather,
payments, invoicing, messaging, geocoding, calendar, and so on — even when the
user already named a provider. Rather than writing integration code from
memory, let Orbit hand you the details that matter: paths, auth header names,
required fields, and the rest. It works in two steps, search then integrate,
and a typical round trip runs ~2,500 tokens and ~15–20s end to end — against
~69,000 tokens for a full vendor OpenAPI spec.

Two REST calls, both `POST`:

1. **Search** (`POST /v1/search`) — describe the task, e.g.
   `{ "q": "send email via SMTP" }`. Returns candidate endpoints, each with an
   `id` and `resourceType` (pass both back verbatim) and an `evaluateGuide`
   grading its fit.
2. **Integrate** (`POST /v1/integrate`) — send the task plus the chosen
   resources (up to 10). Returns a `taskBrief` with `FIT`, `AUTH`, `BASE URL`,
   `STEPS`, and `GOTCHAS` — read the GOTCHAS before writing the client.

Full endpoint schemas, request/response shapes, `taskBrief` fields, and error
handling: [reference/orbit.md](reference/orbit.md).

## `search`

`postman search <type> <query>` finds any Postman entity, searching across
`requests`, `collections`, `workspaces`, `flows`, `specs`, `mocks`,
`environments`, or `documents`. The query can be a keyword or natural language,
and is optional (omit it to list or filter a type outright). Narrow with
`--ownership` and `--filter`, and add `-o json` for the enriched payload. An
empty default-scope result is not proof nothing exists — retry with
`--ownership all` before reporting that.

```bash
postman search requests "where do we validate a user's email?"
postman search collections "payments" --ownership external --filter "visibility=public"
```

Use `postman search <type> -h` for more details — ownership modes, the
`--filter` / `--filter-json` syntax, filter fields per type, and the exact
installed-version flags.

## `context-graph`

The Context Graph is a private, authenticated map of an API ecosystem. It
reconciles Postman specifications, collections, monitors, and mocks; GitHub
repositories, definitions, and call sites; and New Relic deployments, traffic,
and telemetry. These become typed entities joined by sourced relationships such
as `calls`, `depends_on`, `owned_by`, and `monitored_by`.

Use it before a cross-service or potentially breaking change. Name the endpoint,
schema, service, database, deployment, or shared module being changed; the graph
discovers the surrounding scope, including runtime callers and repositories not
checked out locally:

```bash
postman context-graph ask "What depends on billing-api?" --wait
postman context-graph ask "What is the likely blast radius of changing this schema?" --wait
```

Treat the result as a lead, not proof. For consequential work, verify candidates
against source, API definitions, deployment configuration, or telemetry and
cite that evidence. Sources are connected through Postman's Agent Context UI
and refresh nightly; an unconnected or not-yet-ingested source makes absence
inconclusive.

`--wait` polls the asynchronous API and prints the answer. Without it, `ask`
returns an ID for `postman context-graph status <askId>`. Use `--json` for the
structured record; `--timeout`, `--interval`, and `--max-steps` control waiting
and reasoning.

The query runs against the team derived from the API key; there is no workspace
or team selector. Authentication uses `--api-key`, `POSTMAN_API_KEY`, or the
current `postman login` session, in that order.

## After discovery: reusing what was found

`dependency add <type> <nameOrId>` formally adds a collection, environment,
or mock found in another workspace as a dependency of the current one —
the step after `search` finds something worth reusing (e.g., feeding
`application test`'s contract matching), rather than copying it in by hand. It
takes a Postman entity ID. If the Context Graph identifies a service or API to
reuse, locate its collection with `search` first, then pass that entity ID to
`dependency add`.

## Reference

- [Orbit](reference/orbit.md) — public API discovery: the search/integrate
  REST endpoints, request/response shape, `taskBrief` fields, and error
  handling. (Docs at `https://www.buildwithorbit.ai`, REST at
  `https://api.buildwithorbit.ai`.)

For `postman search`, run `postman search <type> -h` — the CLI's own help is
per-type, complete, and always matches your installed version.
