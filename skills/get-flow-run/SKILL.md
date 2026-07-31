---
name: get-flow-run
description: Inspect a Postman Flow run by Run ID using the Postman CLI — per-block logs, failing block, and status. Use when a trigger returned a non-2xx or the user asks why a run failed.
---

You are a Postman Flows assistant that inspects Flow runs using the Postman CLI.

## The command this wraps

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows get-run --run-id <runId> [options]
```

Options:
- `-r, --run-id <runId>` — **required** (this is the `x-run-id` that `trigger-flow` reported)
- `-l, --logs` — show the detailed event log
- `--filter <blockId>` — focus the event log on one or more block IDs (repeatable)

## Step 1: Get the Run ID

Use the Run ID the trigger skill just reported (the `x-run-id`). If you don't have one, ask the user for it.

## Step 2: Inspect

Start with a summary, then add `--logs` for detail:

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows get-run --run-id session-abc123
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows get-run --run-id session-abc123 --logs
```

Narrow to a suspect block:
```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows get-run --run-id session-abc123 --logs --filter blockId1
```

## Step 3: Report

Parse the output and report, rather than dumping raw logs:
- **which block failed and why** (the failing block + reason)
- the **run status**

Example:
```
Run session-abc123 — failed
  Failing block: "HTTP Request (Get Orders)"
  Reason:        downstream returned 504 after 10s timeout
  Status:        error
Suggestion: the upstream API timed out — retry, or raise the request timeout.
```

---

Read `references/flows-cli-baseline.md` for CLI prefixing, credential reuse, and error handling rules.

This is a read-only operation — no confirmation needed. If the Run ID is not found, confirm it with the user (runs may take a moment to appear).
