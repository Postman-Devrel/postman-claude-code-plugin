---
name: flows
description: Runs, deploys, and debugs Postman Flows from the command line — executing a flow file locally, triggering a deployed flow over its webhook, deploying one so it becomes callable, and tracing a failed run to the block that broke. Use when the user names a flow and an action ("run the Checkout flow", "deploy this flow", "why did that flow run fail", "what flows do I have"). Covers `postman flows list`, `run`, `trigger`, `deploy`, `update`, `list-runs`, and `get-run`.
---

# Postman Flows

## Overview

Listing flows, running them, deploying them so they become callable, and
tracing a failed run to the block that caused it — all through
`postman flows`.

## Core knowledge

A flow is a graph of blocks, not a script. That single fact drives the rest of
this skill: a flow has two independent execution paths, and its HTTP response
describes one block rather than the whole graph, so debugging takes a
different command than running.

### Local file vs deployed artifact

`run` and `trigger` are not two ways to execute one flow. Postman Flows has
two Native Git modes, and they are isolated from each other:

- **Cloud View** (the default) syncs flows to Postman Cloud, which is what
  makes them shareable and **deployable** — so Cloud View is the only side
  `deploy`, `trigger`, `update`, `list-runs` and `get-run` ever address.
- **Local View** stores flows as JSON in a local Git repo, updated as they are
  edited. Those flows **cannot be shared or deployed**, have no snapshots, and
  are isolated from the flows in Cloud View.

| | `flows run <path>` | `flows trigger <flowId>` |
| --- | --- | --- |
| Executes | a flow JSON file on this machine | the cloud-deployed flow, via its webhook |
| Returns | status, output, test results, exit code | Run ID + HTTP status + response body |
| Observability | own stdout, `--output`, `--reporters` | `get-run`, per block |
| Environment file | `-e/--environment` | not supported |

`run` exits nonzero on failure, which is what lets a CI job gate on it.
`trigger` goes through the real webhook URL, so it exercises the deployed path
end-to-end — auth and trigger configuration included — and registers a cloud
run that `get-run` can explain block by block.

`postman init` scaffolds `postman/flows/`, and Postman's `flows run` examples
use that path. Note what puts files there: the Git-connected Flows experience
is **desktop-app only**, so `postman/flows/*.json` is written by the desktop
app's Local View, not by the CLI — `workspace push`/`pull` carry no flows
handling whatever else they sync. Don't tell a user to `workspace pull` to
obtain a flow file.

### What deploying buys, and what it requires

Deploying puts the flow in Postman's cloud and attaches an HTTP trigger, which
is what makes it reachable by schedules, webhooks, third-party apps, and other
APIs — the flow stops being something a human opens and becomes callable
infrastructure.

Three preconditions sit outside the CLI, so no flag or retry satisfies them:
the flow must be in Cloud View, its Start block must be configured with an API
request trigger, and its canvas must have a Response block. Check these before
re-running a failed deploy with different arguments.

`--path` is a suffix appended to a generated base URL, not a full URL.

### Inputs: `-i` versus a scenario

A scenario is a named input set stored **in the flow definition**, generated
when someone adds an input to the Start block. Because it travels with the
flow, `-s "Staging"` is reproducible across invocations and across people,
where `-i key=value` is per-invocation. Start-block inputs can be declared
secret, which is what `--show-secrets` unmasks in dry-run output.

Precedence: `-s` supplies payload, headers, and query; `--headers` and
`--query` override it; `-i`/`-f` override its values.

### Identifiers

`flows list` is the only way to turn a flow name into an id —
`.postman/resources.yaml` maps collections to cloud ids but has no flows
section, so there is nothing local to read. Both `list` and `list-runs`
**require** `-w/--workspace`; take that id from `workspace.id` in
`.postman/resources.yaml`, which `bootstrap` records.

Run IDs have no single documented shape (`session-abc123` and `main/1a123ab1`
both appear in Postman's own material). Use whatever `trigger` or `list-runs`
printed, verbatim, and apply the same rule to flow ids.

### Plan and permission gating

`flows run` is documented as Enterprise-only, and the cloud subcommands need
`postman login`. `Access denied. Please check your permissions for the
specified resource.` on *every* workspace is a credential-scope or plan
signal, not a wrong-workspace signal — and never means the workspace has no
flows.

## Deploying: propose, confirm, then verify

Deploy is the one multi-phase workflow here, because it is mutating and
because its result is only half-useful without the follow-up check.

1. **Resolve the id.** `flows list --workspace <id> --filter "Checkout"`. On
   multiple matches, show name + id + last-updated and let the user pick.
2. **Propose the path.** Derive it from the flow name — "Checkout" →
   `/checkout` — so the user is confirming a concrete value rather than
   answering an open question. Raise `--auth` here if the trigger will be
   reachable by anyone who learns the URL.
3. **Confirm, then run** `flows deploy <flowId> --path /checkout`.
4. **Report the Trigger URL and whether the trigger is enabled.** A deploy can
   land with the trigger off, which looks identical to a broken deploy at call
   time. If it is off, offer `flows update <flowId> --trigger on`.

When the deploy existed only so the flow could be run, trigger it in the same
turn and report the Run ID — deploy-then-trigger is one job.

## Running and triggering

Show the command before running it, and map the request onto flags: inputs to
`-i`, a payload file to `-f`, query to `-q`, headers to `--headers`, a named
scenario to `-s`.

```bash
postman flows run postman/flows/checkout.json -i amount=4200
postman flows trigger <flowId> -i amount=4200
```

`run` is documented as Enterprise-only, so check the plan before building a
workflow on the local path. Where the flow is already in Cloud View, `trigger`
covers the gap; a Local View flow has no such fallback, since it cannot be
deployed.

`-n/--dry-run` on `trigger` prints the resolved URL and payload without
sending — worth reaching for when a flow writes to real systems, since a
trigger is not a read-only probe. For CI, `--output json` and `--reporters
html` persist results, and `--workspace` is required if the flow contains
connector blocks (it fails at the block, not at startup).

Report the Run ID on every trigger, including successes; it is the only handle
on the run afterwards.

Two failures are recoverable rather than terminal, and both recover through a
confirmed mutation. A 404 hinting `To deploy it, run: postman flows deploy`
means the flow exists but was never deployed — offer the deploy above, then
re-trigger. A disabled-trigger error means it is deployed but not accepting
calls — offer `flows update <flowId> --trigger on`, then trigger.

## Debugging a run

A trigger's response body is the Response block's output. A flow can answer
200 with a failed block upstream, and a 500 says nothing about which block
produced it — so read the run, not the response.

```bash
postman flows list-runs --workspace <id> --flow <flowId> --range 3d
postman flows get-run --run-id <runId> --logs
```

`list-runs` recovers a Run ID nobody wrote down; its `--range` defaults to
`1h`, so widen it before concluding a run is missing. Start `get-run` without
`--logs` and add them when the summary does not explain the failure;
`--filter` narrows to a block-id prefix.

Report the failing block, the reason, and the run status:

```
Run session-abc123 — failed
  Failing block: "HTTP Request (Get Orders)"
  Reason:        downstream returned 504 after 10s timeout
  Status:        error
```

## Critical Rules

1. **Resolve ids, never infer them.** A name is not an id, and no id format is
   documented well enough to validate against. Ambiguous name → present
   candidates and ask.
2. **`deploy` and `update` need explicit confirmation.** They change what the
   flow does for every caller: a deploy exposes a trigger path, `--trigger
   on|off` starts or stops accepting calls, and `--auth off` removes
   authentication from a live trigger.
3. **Report the failing block, not the log.** `--logs` output is input to your
   analysis; the user needs the block, the reason, and the status.
4. **Surface CLI errors verbatim** and read them literally. "Flow file not
   found", a required-option error, and "Access denied" have three different
   fixes, and only the last is about permissions.
5. **A missing or unauthenticated CLI is `bootstrap`'s job** — route there
   rather than improvising an install or a second login.

## Anti-patterns

1. **Don't substitute `run` for `trigger` when a flow isn't deployed.** A
   green local run says nothing about the deployed path a caller hits, and a
   Local View flow cannot be deployed at all.
2. **Don't hunt for a different workspace id when access is denied across
   every workspace you try.** A blanket denial points at the credential's
   scope or the plan, not at the id.
3. **Don't pass `-x/--suppress-exit-code` in CI.** It makes a failed flow
   report success to the pipeline, which removes the only thing gating it.
4. **Don't put reusable inputs on the command line.** A payload that matters
   more than once belongs in a Start-block scenario, where it travels with the
   flow.

## Reference

- [Flows CLI flags](reference/flow_cli_flags.md) — full flag tables per
  subcommand, the BETA dataset-iteration flags, and the short-flag collisions
  between subcommands. Read before composing a command with flags not shown
  above.
- `bootstrap` skill — CLI install, login, and the workspace id these commands
  require.
- `api-discovery` skill — `postman search flows` finds a flow by text across
  Postman, a different dataset from `flows list`'s workspace enumeration.
