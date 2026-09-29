---
name: api-testing
description: Runs tests against an API from the command line — a single ad-hoc request, a full collection of pm.test assertions, or matching real captured app traffic against a collection contract. Use when the user asks to "test this endpoint," "run this collection," "check the API still works," or "verify my app's requests match the contract." Covers `postman request`, `postman collection run`, and `postman application test`. Depends on bootstrap when the target is a cloud collection or workspace-bound environment; a bare URL or local collection needs nothing from bootstrap.
---

# API Testing

## Overview

Three tools, matched to what already exists:

| Have | Use |
| --- | --- |
| Just a URL to check, with no saved request | `postman request` |
| A request already saved in a collection | `postman collection run <collection-path> -i <request-id-name-or-path>` |
| A collection with `pm.test` assertions saved in it | `postman collection run` |
| A real app (browser flow, CLI, service) whose traffic should match a collection's contract | `postman application test` |

Don't reach for the heavier tool when the lighter one already answers the
question — a one-off endpoint check doesn't need a collection, and a
collection run doesn't need Playwright.

## `postman request` — over curl, not instead of testing

A single request with Postman's resolution built in: `-e` resolves
`{{variables}}` from an environment file the same way a collection run
would, `--auth-*` flags cover basic/bearer/digest/oauth/aws/etc. without
hand-building headers, and `--retry`/`--timeout` handle flaky endpoints.
`--script-post-request` can run `pm.test(...)` assertions inline — the exit
code counts *failed assertions*, not just HTTP status, so a 200 with a
failing test still exits nonzero. Useful for a quick check or a CI health
check; not the place to accumulate assertions that should outlive one
command — those belong saved in a collection.

Before constructing a URL, headers, auth, and body on the command line, look
for a matching `*.request.yaml` under `postman/collections/`. If it exists,
execute the saved request through its collection:

```bash
postman collection run "postman/collections/Orders API" -i "create order"
```

Do not copy the saved YAML fields into `postman request`; that bypasses the
collection's inherited variables, auth, scripts, and maintained payload. The
`postman request` positional target is a URL, not a `.request.yaml` path. When
there is no saved request but its body already lives in a separate file, keep
the file as the source of truth with `--body @path/to/payload.json` instead of
inlining its contents.

## `collection run` — the assertion suite

Debugging a request's behavior during a run (why a `pm.test` failed, what a
request actually sends) means reading the request's own YAML — see the
`collection-schema-v3` skill for that file format before assuming a field's
shape.

Runs every request in a collection (or a subset via `-i`, repeatable),
executing whatever `pm.test` scripts are already saved in it.
`-d`/`--iteration-data` (or the beta `--iteration-data-dataset` +
`--iteration-data-view` pair) drives data-driven runs across a CSV/JSON
file or a Postman Dataset. `-r junit,html` for CI-consumable reports.
`--use-mock`/`--mock` redirects the run at a mock instead of a real backend
(see the `api-mocking` skill) — reach for this to test request/assertion
logic without depending on a live service.

## `application test` — contract-matching real traffic

This doesn't send its own requests. It runs your existing test command
(`--command "npx playwright test"`, or config-driven via
`postman.config.cjs` targets), captures the network traffic that command
generates, and matches/asserts it against your Postman collections —
answering "did my app's actual calls conform to the contract," not "does
this endpoint respond correctly." `--capture-only` skips the matching step
entirely and just exports what was captured as a new v3 collection,
organized by host — a way to bootstrap a collection from real traffic
rather than authoring one from scratch. Results upload to Postman
automatically after each run; `--report-events=false` skips that for a run
that shouldn't be recorded.

## Critical Rules

1. **Don't reach for `application test` for something a plain
   `collection run` covers.** It exists specifically for matching *captured*
   app traffic (via Playwright or similar), not for driving requests itself.
2. **`postman request`'s exit code reflects failed `pm.test` assertions, not
   HTTP status alone.** A nonzero exit on a 200 response usually means a
   post-request script assertion failed, not a network problem.
3. **Assertions meant to be reused belong in the collection, not on the
   command line.** A `--script-post-request` test on `collection run` runs
   once and leaves nothing for the next person; save it as a `pm.test` in
   the request instead.
4. **`--use-mock` is the way to test without a live backend** — prefer it
   over standing up ad hoc fakes or skipping tests that need a dependency.
5. **Reuse a saved request instead of reconstructing it.** If a matching v3
   request exists, use `collection run <collection-path> -i <request>`; reserve
   `postman request` for genuinely ad-hoc requests.

## Verification

State the actual result (pass/fail counts, exit code), not just that the
command ran. For `application test`, state whether it ran in match mode or
`--capture-only` — they answer different questions and shouldn't be
reported the same way.
