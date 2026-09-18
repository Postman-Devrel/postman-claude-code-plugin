---
name: api-mocking
description: Stands up a fake backend that behaves like a real API — from a collection or an OpenAPI spec, running locally or pushed to Postman's cloud for a durable URL — plus request-time scenario and status-code overrides for testing failure paths. Use when the user asks to "mock this API," "create a mock server," "fake the backend," "run tests without hitting the real API," or "simulate an error/out-of-stock response." Covers `postman mock`. Depends on bootstrap for the workspace id only once a mock is pushed to the cloud (`-w`, or the workspace linked in `.postman/resources.yaml`) — generating and running a mock locally needs nothing from bootstrap.
---

# API Mocking

## Overview

A mock is two files on disk: `config.yaml` (name, port, list of scenarios)
and `default.js` — a plain Node HTTP server, and the mock itself, not a
wrapper around one. Because it's just code, generating, inspecting, running,
and calling a mock are all local and work for a logged-out guest. Only
sharing it — pushing it to the cloud and deploying a durable URL — needs
`postman login`.

Local and cloud aren't a choice made once at `generate` time. Every mock
starts as a local folder; `mock push` promotes any existing local folder to
the cloud later, whether or not `-w` was passed at generate. Reach for cloud
only when something other than you needs to hit this mock over the network —
a teammate, a CI job elsewhere, a webhook sender. A purely local mock
answering a `postman request` on your machine never needs it.

## Process

1. **Generate.** `postman mock generate -n NAME --port N` with no source
   scaffolds a complete sample cart mock — the fastest way to a server that
   already answers, useful whenever the point is exercising mock *behavior*
   rather than a specific API's shape. Pass a real source —
   `postman mock generate SOURCE -n NAME --port N`, where `SOURCE` is a
   collection folder or an `openapi.yaml` — when the endpoints need to mirror
   an actual API. Either form writes `config.yaml` + `default.js` into
   `postman/mocks/NAME/`. Adding `-w <workspaceId>` also creates the mock in
   that workspace on top of writing the local files — it doesn't replace the
   local write, and it requires being logged in.
2. **Run it.** `postman mock run ./postman/mocks/NAME` starts
   `Mock server started at http://localhost:PORT`. If the port in
   `config.yaml` is taken and `--port` wasn't passed explicitly, it falls
   back to a free OS-assigned port instead of erroring — read the real port
   off that line rather than assuming the configured one. Naming `--port`
   explicitly makes a taken port a hard `Port already in use` error instead.
3. **Call it.** Plain `postman request localhost:PORT/route` returns the
   default scenario's response. Two headers change that per-request, with no
   restart needed: `x-mock-scenario: <name>` selects a different scenario
   (the valid names live in `config.yaml` — `mock get` only ever shows the
   default one), and `x-mock-response-code: <code>` returns that status
   instead. A wrong route and a wrong scenario name both come back as
   `Endpoint not defined` — indistinguishable from the message alone.
   There's no hot reload: a `default.js` edit does nothing until you
   Ctrl+C the running server and `mock run` it again.
4. **Push it, if it needs to leave your machine.**
   `postman mock push ./postman/mocks/NAME` is safe to re-run — `Created`
   the first time, `Updated` after. It returns a cloud ID that is a *new*
   identifier, not the `id` already sitting in `config.yaml` — see
   [The three identifiers](#the-three-identifiers) below. It also modifies
   `.postman/resources.yaml`; commit that change.
5. **Deploy it, for a URL that outlives your terminal.**
   `postman mock deploy CLOUD_ID -s SLUG -y --auto-deploy` prints
   `https://SLUG.mock.<team-domain>.postman.dev`. Deployed private by
   default — callers need an API key — add `--public` only when the mock
   should be reachable by anyone with the URL. `-y` alone accepts
   private/auto-deploy-off; without `--auto-deploy`, a later `push` doesn't
   change what's actually being served until you `deploy` again.
6. **See who's calling it.** `postman mock get CLOUD_ID --json` returns
   `.mockServerId`; feed that into `postman mock log MOCK_SERVER_ID --json`
   for call entries. An empty log means the URL genuinely hasn't been hit —
   a rejected caller still shows up, recorded with its failing status code.
7. **Tear down.** `postman mock delete ./path --yes` (local) or
   `postman mock delete CLOUD_ID --yes` (cloud) — both refuse while the
   thing is still alive, so stop the local run or bring the deployment down
   first. Cloud delete doesn't touch `.postman/resources.yaml`; drop that
   line by hand afterward or the repo keeps claiming a mock that's gone.

To point real request/assertion runs at a mock instead of hand-editing
base-URL variables, see the `api-testing` skill's `--use-mock`/`--mock`
flags on `collection run`.

## The three identifiers

`config.yaml`'s local `id`, the cloud ID `push` returns, and the
`mockServerId` from `get CLOUD_ID --json` are three different values, in the
order they become available. Only the second and third are lookups —
`push` is a creation, not a promotion, so passing the `config.yaml` id to any
cloud command is passing the wrong key, not a stale one.

## Critical Rules

1. **Every gated cloud command fails the same way:**
   `Authentication required. Run postman login or provide --api-key`,
   exit 1, nothing half-done. Whether a command is gated is decided by what
   you pass it, not the verb — `mock get`/`mock run` take either a local
   path (ungated) or a cloud ID (gated); `mock list` is gated only when
   called with no path.
2. **`push` is what moves an existing local mock to the cloud — `-w` at
   `generate` time is optional, not a fork you must choose up front.** A
   mock built as a guest can be pushed and deployed later with no rework.
3. **`--public` on `deploy` is the one action here with real exposure** — it
   stands up a server anyone with the URL can hit, with no API key. The
   default (private) is the safe one; confirm intent before adding it.
4. **Don't reuse the `config.yaml` id for a cloud command, and don't invent
   a `mock generate` flag for regenerating in place.** The reference for
   this CLI documents editing `default.js` and restarting as the way to
   change a running mock's behavior — no in-place "update from source" verb
   is documented. Run `postman mock generate -h` before assuming one exists
   rather than guessing a flag name.
5. **`-w`/`--workspace` only exists on `generate`, `list`, `push`, and
   `deploy`.** `get`, `run`, `log`, and `delete` already take a path or an
   id that says where the mock is — there's nothing left for `-w` to
   resolve on those.

## Verification

A mock isn't done because `generate` or `run` exited 0 — hit it with
`postman request` and check the actual status/body, or `mock get CLOUD_ID
--json` for a cloud one, then state whether it ended up local or cloud, and
(if deployed) private or public. For a scenario/status-code check, confirm
the header actually changed the response — a typo'd scenario name returns the same
`Endpoint not defined` as a wrong route, so a passing exit code alone proves
nothing.
