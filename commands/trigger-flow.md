---
description: Trigger (run) a deployed Postman Flow with inputs, and deploy-then-trigger it if it isn't deployed yet
allowed-tools: Bash, Read
---

Trigger a deployed Postman Flow from natural language, using the Postman CLI. Follow the `trigger-flow` skill.

## Inputs (from the user's message)
- The flow (a 24-char ID, or a name to resolve via `list-flows`)
- Any inputs / query params / headers / scenario
- The workspace ID (ask if a name needs resolving and you don't have it)

## Steps
1. Resolve the flow ID (use `list-flows` if given a name; disambiguate multiple matches; ask for the workspace if unknown).
2. Build the flags from natural language: `-i k=v`, `-q k=v`, `--headers k=v`, `-s "<scenario>"`.
3. Show the command, then run it:
   ```bash
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows trigger <flowId> -i amount=4200
   ```
4. Report the **Run ID**, **HTTP status**, and **response body**.
5. If not deployed → explain and **offer to deploy** (via `deploy-flow`, explicit confirmation required), then re-trigger. If the trigger is disabled → offer `postman flows update <flowId> --trigger on` (confirm), then trigger.
6. On a non-2xx response → surface status + body and offer `get-flow-run --run-id <id>` for per-block detail.

Always prefix CLI calls with `POSTMAN_CLI_SOURCE=claude-code-plugin`. Reuse existing `postman login` credentials — never authenticate twice. Confirm before any mutating action (deploy, enable trigger).
