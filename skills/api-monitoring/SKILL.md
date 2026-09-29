---
name: api-monitoring
description: Creates, schedules, and manages Postman Monitors — recurring checks against a live API — triggers ad hoc runs, inspects job/run history to diagnose failures, and hosts self-hosted execution runners for monitors on a private network. Use when the user asks to "set up a monitor," "run this monitor now," "check monitor results," "pause/resume a monitor," or "set up a runner for our internal APIs." Covers `postman monitor` (create, update, delete, list, get, pause, resume, run, jobs, runs) and `postman runner` (start, list, regions).
---

# API Monitoring

## Overview

A Monitor is a recurring, scheduled check against a live API. The CLI now
owns its full lifecycle: `monitor create`/`update`/`delete`/`pause`/`resume`
manage the schedule and configuration, `monitor list`/`get` discover and
inspect existing ones, `monitor run` triggers an ad hoc run, and `monitor
jobs`/`monitor runs` inspect what actually happened during a run. There is
no remaining task here that has to go through the Postman app.

`postman runner` is a separate, infrastructure-level concern: it starts a
self-hosted execution agent so Monitor runs can reach APIs that live behind
a private network Postman's cloud can't reach directly, and it lists the
values (Postman regions or self-hosted runner ids) that `monitor
create`/`update --runner` accepts.

## Creating and scheduling a monitor

`monitor create -c <collectionId>` is the minimum — name defaults to the
linked collection's own name. Workspace comes from `-w`, or falls back to
the workspace named in the local `.postman/resources.yaml` manifest;
without either, creation fails. `--schedule <cron>` plus `--timezone`
(defaults to the host machine's zone) set when it fires; `--runner`
(repeatable) says where from — a Postman region name (`postman runner
regions`) or a self-hosted runner's id (`postman runner list`), and both
can be mixed in the same monitor. `--notify-email` (repeatable) and
`--notification-limit` control failure alerts. The run itself is shaped by
the same options as a collection run — `--retry` (service caps at 2),
`--timeout`, `--delay`, `--strict-ssl`/`--insecure`,
`--follow-redirects`/`--block-redirects`, and dataset iteration via
`--dataset-id`/`--dataset-view-id`/`--iteration-count`/
`--iteration-strategy`. Creation triggers an immediate run by default; pass
`--no-run-now` to skip that.

## Updating, pausing, and deleting

`monitor update <monitorId>` takes the same schedule/runner/notification/
run-option flags as `create`, plus `--clear-notifications` to wipe every
recipient. It cannot change the linked collection or environment — delete
and recreate the monitor instead — and it does not pause or resume; use
`monitor pause`/`monitor resume` for that. `monitor delete <monitorId>`
prompts for confirmation unless `-y`/`--yes` is passed, and is permanent.

## Discovering and inspecting monitors

`monitor list` filters by `-w`/`-c`/`--environment`/`--owner`/`--team`/
`--active`. `--runner <id>` filters to a *self-hosted* runner id (not a
Postman region) and can't be combined with the other filters. Page with
`--limit`/`--cursor`; `--offset` is accepted by the service but silently
ignored, so the CLI rejects it locally rather than returning a page that
looks right but isn't — use `--cursor` from the previous page's response.
`--columns` picks which fields show, `-f`/`--filter` matches on name within
the page already returned (not a server-side search), and `--sort name|active`
orders it. `monitor get <monitorId>` shows one monitor's full configuration.

## Triggering a run

`monitor run <monitorId>` runs an existing Monitor synchronously and prints
the result — useful in CI to get a pass/fail right after a deploy rather
than waiting for the next scheduled tick. `-t/--timeout` (default 15
minutes) caps how long the CLI waits for completion; a timeout hit here is
the CLI giving up on waiting, not the Monitor itself failing. `--async`
submits the run and returns immediately with its job id and Postman URL
instead of waiting at all — reach for this over a long `-t` when the caller
doesn't need the verdict inline. `--json` prints only the verdict as JSON,
for scripting. `-x/--suppress-exit-code` overrides the default
fail-on-failed-run exit code, for a caller that wants to see failures
without breaking a pipeline step.

## Diagnosing a run

`monitor jobs list <monitorId>` lists a monitor's recent jobs; `monitor jobs
get <jobId>` reports one job's terminal state and its per-region run
outcomes — a monitor with runners in multiple regions runs once per region
per job. `monitor runs get <runId>` goes one level deeper: which test
assertions ran during one attempt, which failed, and why. Reach for these
instead of re-running blind after a `-t` timeout, or whenever the task is
explaining *why* a monitor failed rather than just that it did.

## Private (self-hosted) runners

A private runner — the CLI's `runner regions` calls the same thing a
"private-runner" value — is an agent you run inside your own network so
Monitor traffic originates there instead of from Postman's cloud IPs. Reach
for one only when the monitored API sits behind a VPN, firewall, or on-prem
network that Postman's cloud can't reach directly; a public API should just
use a Postman region (`--runner us-east`, etc.) since that needs no
infrastructure of your own to run or maintain.

`runner start --id <id> --key <key>` (from the Postman app) registers a
runner that executes monitor runs from your own infrastructure instead of
Postman's cloud. Extra
flags cover the runner's own networking: `--region eu` for EU residency,
`--proxy`/`--egress-proxy`/`--egress-proxy-authz-url` for outbound routing,
`--ssl-extra-ca-certs` for a private CA, and `--metrics`/`--metrics-port`
for a health-check endpoint. Analytics are sent by default; `--no-report-events`
opts out. `runner list` shows the team's registered self-hosted runners —
feed an id from here into `monitor create/update --runner` or `monitor list
--runner`. `runner regions` lists the Postman-region and private-runner
values valid for `--runner` on `monitor create`/`update`, including a
static IP where one is configured — check here before guessing a region
string.

## Critical Rules

1. **`update` can't move a monitor to a different collection or environment,
   and doesn't pause/resume it.** Delete and recreate for the former; use
   `pause`/`resume` for the latter.
2. **A `monitor run -t` timeout is a wait cap, not a monitor failure.**
   Don't report "the monitor failed" from a timeout without checking
   `monitor jobs get`/`monitor runs get` (or the Postman app) for what the
   run actually did after the CLI gave up waiting — or avoid the wait
   entirely with `--async`.
3. **`--runner` on `monitor create`/`update` takes a region name or a
   self-hosted runner id — check `runner regions`/`runner list` before
   guessing a string,** and don't suggest `runner start` unless the target
   API genuinely isn't reachable from Postman's cloud.
4. **`monitor list --offset` doesn't work — use `--cursor`,** and
   `--runner` there can't be combined with the other filters.
5. **`monitor delete` is permanent.** Confirm intent before passing `-y` to
   skip its prompt.

## Verification

State the monitor/job/run id and the actual pass/fail result or
configuration change, not just that the command exited. For `run`, state
whether it completed synchronously or was submitted `--async` (a job id is
not yet a verdict — resolve it with `monitor jobs get` before reporting a
result). If a self-hosted runner was started, confirm it registered (the
Postman app, or `runner list`, shows it as connected) before assuming
monitor runs will route through it.
