---
description: Inspect a Postman Flow run by its Run ID — per-block logs, failing block, status, and credits consumed
allowed-tools: Bash, Read
---

Inspect a specific Postman Flow run using the Postman CLI. Follow the `get-flow-run` skill.

## Inputs (from the user's message)
- The Run ID (the `x-run-id` that `trigger-flow` reported; ask if unknown)
- Optionally a block ID to focus on

## Steps
1. Take the Run ID.
2. Run a summary, then add `--logs` for detail:
   ```bash
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows get-run --run-id <runId>
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows get-run --run-id <runId> --logs
   ```
   Narrow to a block with `--filter <blockId>`.
3. Report **which block failed and why**, the **run status**, and **credits consumed** when the run history exposes it (say so if it doesn't, rather than inventing a number).

Read-only: no confirmation needed. Prefix CLI calls with `POSTMAN_CLI_SOURCE=claude-code-plugin`. Reuse existing `postman login` credentials.
