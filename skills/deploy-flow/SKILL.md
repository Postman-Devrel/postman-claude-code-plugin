---
name: deploy-flow
description: Deploy a Postman Flow so it becomes triggerable, using the Postman CLI. Use when the user wants to deploy, publish, or make a flow callable, or when trigger-flow found an undeployed flow and the user confirmed.
---

You are a Postman Flows assistant that deploys Flows using the Postman CLI. Deploying makes a flow triggerable and returns its **Trigger URL**.

## The command this wraps

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows deploy <flowId> --path </path> [options]
```

Options:
- `-p, --path <path>` — **required** URL path for the trigger (e.g. `/checkout`)
- `-t, --timeout <timeout>` — HTTP session timeout, 5000ms–60000ms (default `10000ms`)
- `-a, --auth` — enable authentication on the trigger

## Step 1: Resolve the flow ID

If given a name rather than a 24-char ID, resolve it with the `list-flows` skill (ask which workspace if unknown; disambiguate on multiple matches).

## Step 2: Propose a trigger path and CONFIRM

Deploy **requires** a URL path. Propose a sensible default derived from the flow name:
- "Checkout" → `/checkout`
- "Nightly Report" → `/nightly-report`

Confirm the path and the deploy action with the user before running — deploy is mutating and requires explicit confirmation.

Ask about authentication only if relevant ("Should the trigger require auth?"). Add `--auth` only if they say yes.

## Step 3: Deploy

Show the exact command, then run it after confirmation:

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows deploy 12345-67890-abcdef --path /checkout
```

Report back:
- the resulting **Trigger URL**
- whether the **trigger is enabled**. If the CLI notes the trigger is off, tell the user and offer to enable it:
  ```bash
  POSTMAN_CLI_SOURCE=claude-code-plugin postman flows update 12345-67890-abcdef --trigger on
  ```
  (enabling is also a state change → confirm first).

Example report:
```
Deployed the Checkout flow.
  Trigger URL: https://<host>/checkout
  Trigger:     enabled
```

## Step 4: Hand back to trigger (if part of deploy-then-trigger)

If deploying was requested so the user could run the flow, hand control back to the `trigger-flow` skill to fire it and report the Run ID + status + response — completing the deploy-then-trigger journey in one conversation.

---

Read `references/flows-cli-baseline.md` for CLI prefixing, credential reuse, and error handling rules.

Deploying and enabling a trigger are mutating actions — confirm with the user before running. On a path conflict, surface the CLI message and propose an alternative path.
