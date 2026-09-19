---
name: performance-testing
description: Load-tests a collection with concurrent virtual users, a chosen load profile, and pass/fail thresholds on latency or error rate — run locally or on Postman's cloud runners. Use when the user asks to "load test this API," "run a performance test," "check how this holds up under load," or "benchmark this collection." Covers `postman performance run`. This generates real traffic against a real target — confirm the target and scale before running, the same way any action with effects outside this session gets confirmed.
---

# Performance Testing

## Overview

`performance run <collectionId>` is not `collection run` with more
iterations — it's a dedicated load-test mode: many virtual users hitting the
collection concurrently for a set duration, shaped by a load profile, scored
against thresholds you define, on infrastructure you choose. The collection
under test is authored the normal way — see the `collection-schema-v3` skill
if it needs edits before the load test is meaningful (e.g. an assertion
that would fail every VU's request identically).

## Core knowledge

- **Load profile is what you're actually testing.** `fixed` holds steady
  concurrency (does this hold up at N users, sustained); `ramp-up` increases
  gradually (where does it start to degrade); `spike` bursts suddenly (does
  a sudden surge break it); `peak` sustains near-maximum load (does it
  survive staying there). Pick based on the failure mode being probed, not
  by default.
- **`--runner` chooses where load originates.** `local` runs from the
  current machine/CI runner — bounded by its own resources, fine for
  internal or low-scale targets. `postman-cloud` runs from Postman's
  infrastructure — needed for realistic external-scale load, or once local
  resources would cap the achievable VU count. `postman-cloud-static-ip`
  is the same, from a static-IP range — needed when the target allowlists
  by IP.
- **`--pass-if "less_than(p95, 500)"` turns a load test into a gate.**
  Metrics: `avg`, `p90`, `p95`, `p99`, `error_rate`, `rps`. Checked after the
  run completes, not enforced live — a bad configuration still generates its
  full load before the gate fails.
- **`--use-mock` points the test at a mock instead of a real backend** — for
  load-testing collection/script logic itself, or to baseline mock-only
  latency and isolate app/network slowness from what the mock adds.
- **`--setup-collection`/`--teardown-collection`** (cloud runner only) run
  once before/after the whole test — for provisioning or cleanup, not
  per-iteration setup.
- **`--dataset-id`/`--dataset-view-id`** drive iteration data from a Postman
  Dataset instead of a flat `--data-file`; `--dataset-distribution` controls
  whether rows are spread round-robin, fixed, or randomly across VUs.

## Critical Rules

1. **Running this against a real, non-mock backend generates real load with
   real consequences — confirm the target, VU count, and duration with the
   user before running,** the same way any action with effects outside this
   session gets confirmed. Default to a low `--vu-count` and short
   `--duration` for a first run against anything live, or point it at a mock
   (`--use-mock`) when the goal is testing the collection, not the backend.
2. **A `--pass-if` gate doesn't stop the load early.** The full VU count and
   duration run regardless of whether the threshold will ultimately pass —
   plan for that cost, don't assume a failing gate means less traffic was
   sent.
3. **Cloud runners come from Postman's IP ranges.** Before assuming a
   `postman-cloud` run will reach a target, check whether it's IP-allowlisted
   — use `postman-cloud-static-ip` if so, rather than discovering the
   mismatch as a wall of connection failures.

## Verification

State the actual metrics the run produced (p95, error rate, rps — whatever
the `--pass-if` checked, plus the ones it didn't) and whether the gate
passed, not just that the run completed. State which runner actually
executed it (`local`/`postman-cloud`/`postman-cloud-static-ip`) — that
determines whether the numbers reflect the target's real-world reachability
or only local-network conditions.
