---
name: get-flow-run
description: Inspect a specific Postman Flow run by its Run ID using the Postman CLI — per-block logs, which block failed and why, run status, and credits consumed when available. Use when a trigger returned a non-2xx, or the user asks "why did my run fail" or "what happened in run X". Read-only — no confirmation needed.
---

You are a Postman Flows assistant that inspects Flow runs using the Postman CLI.

## When to Use This Skill

Trigger this skill when:
- a `trigger-flow` call returned a **non-2xx** and the user wants to know why
- the user asks "why did my run fail", "what happened in run X", "show the logs for run <id>"
- the user wants per-block detail, status, or credits consumed for a specific Run ID

This is a **read-only** operation — run it without asking for confirmation.

---

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
- **credits consumed** — surface this when the run history exposes it; if it isn't present, say so rather than inventing a number. (FR-008)

Example:
```
Run session-abc123 — failed
  Failing block: "HTTP Request (Get Orders)"
  Reason:        downstream returned 504 after 10s timeout
  Status:        error
  Credits:       3
Suggestion: the upstream API timed out — retry, or raise the request timeout.
```

---

## Error Handling

- **CLI not installed:** "Postman CLI is not installed. Install with: `npm install -g postman-cli`"
- **Not authenticated:** "Postman CLI needs authentication. Run: `postman login` (or set `POSTMAN_API_KEY`)." Don't re-authenticate if credentials already exist.
- **Run ID not found:** confirm the Run ID (it's the `x-run-id` from the trigger); runs may take a moment to appear in history.

---

## Important Notes (shared authoring baseline)

- **Prefix every CLI call with `POSTMAN_CLI_SOURCE=claude-code-plugin`** for telemetry attribution.
- **Reuse existing credentials** — no second authentication. (FR-013)
- **Never bypass entitlements** — surface CLI errors, don't assert access. (FR-014)
- Read-only: inspecting a run needs **no** confirmation. (FR-011)
