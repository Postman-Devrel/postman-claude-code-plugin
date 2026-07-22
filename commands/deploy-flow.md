---
description: Deploy a Postman Flow so it becomes triggerable, proposing and confirming a trigger path
allowed-tools: Bash, Read
---

Deploy a Postman Flow using the Postman CLI. Follow the `deploy-flow` skill.

## Inputs (from the user's message)
- The flow (a 24-char ID, or a name to resolve via `list-flows`)
- Optionally a desired trigger path and whether auth is required

## Steps
1. Resolve the flow ID (use `list-flows` if given a name; ask for the workspace if unknown).
2. Propose a trigger path derived from the flow name (e.g. "Checkout" → `/checkout`) and **confirm the path + the deploy action** with the user — deploy is mutating and MUST NOT run without explicit confirmation.
3. Show the command, then run it after confirmation:
   ```bash
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows deploy <flowId> --path /checkout
   ```
4. Report the **Trigger URL** and whether the **trigger is enabled**. If it's off, offer `postman flows update <flowId> --trigger on` (confirm first).
5. If this was part of a deploy-then-trigger request, hand back to `trigger-flow` to run it.

Always prefix CLI calls with `POSTMAN_CLI_SOURCE=claude-code-plugin`. Reuse existing `postman login` credentials — never authenticate twice.
