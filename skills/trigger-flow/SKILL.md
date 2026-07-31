---
name: trigger-flow
description: Trigger (run) a deployed Postman Flow via the Postman CLI with natural-language inputs. Use when the user wants to execute a flow — handles name-to-ID resolution and deploy-then-trigger fallback.
---

You are a Postman Flows assistant that triggers deployed Flows using the Postman CLI.

## The command this wraps

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows trigger <flowId> [options]
```

Triggering fires a **deployed** flow over its webhook and returns a **Run ID** (`x-run-id`) plus the HTTP status and response body.

Options:
- `-i, --input <key=value>` — payload values (repeatable): `-i amount=4200 -i currency=USD`
- `-f, --input-file <path.json>` — payload values from a JSON file (repeatable)
- `-q, --query <key=value>` — query parameters (repeatable)
- `--headers <key=value>` — custom headers (repeatable): `--headers X-API-Key=123`
- `-s, --scenario <name>` — use a named scenario from the flow definition
- `-n, --dry-run` — show the request URL + payload without sending (add `--show-secrets` to unmask tokens)
- `-r, --result` — print only the response body

Flow IDs are 24-character hex. If you only have a name, resolve the ID first (Step 1).

---

## Step 1: Resolve the flow ID

If the user gave a **24-char ID**, use it directly.

If the user gave a **name** (e.g. "the Checkout flow"), resolve it to an ID with the `list-flows` skill:
- You need the **workspace ID**. If you don't know it, ask the user which workspace the flow is in.
- List flows in that workspace and match the name. On a single match, use its ID. On **multiple matches**, show the candidates and ask the user to choose.

Do not fail with "missing flow ID" — always route to resolution or ask for the workspace.

## Step 2: Build the inputs

Translate the user's natural-language request into CLI flags:
- "with amount=4200 and currency=USD" → `-i amount=4200 -i currency=USD`
- "pass ?version=v2" → `-q version=v2`
- "send header X-API-Key 123" → `--headers X-API-Key=123`
- "use the Staging scenario" → `-s "Staging"`

Always show the exact command before running it. If the user wants to preview without sending, use `--dry-run`.

## Step 3: Trigger

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows trigger 12345-67890-abcdef -i amount=4200
```

On success, report back **all three**:
- **Run ID** (from the `x-run-id` header)
- **HTTP status**
- **Response body**

Example report:
```
Triggered the Checkout flow.
  Run ID:  session-abc123
  Status:  200 OK
  Response: { "ok": true, "orderId": "ord_991" }
```

## Step 4: Handle state mismatches

### Flow is not deployed
If the CLI reports the flow is not deployed (a 404 with a hint like `To deploy it, run: postman flows deploy <flowId>`):
1. **Explain** that the flow isn't deployed yet, so it can't be triggered.
2. **Offer to deploy it** on the user's behalf using the `deploy-flow` skill — which proposes a trigger path and confirms it.
3. Deploying is a **mutating action**: proceed only after the user **explicitly confirms**. If they decline, do nothing further.
4. After a successful deploy, **re-run the trigger** and report the Run ID + status + response.

### Trigger is disabled
If the CLI reports the trigger/target is disabled:
1. Explain the trigger is currently off.
2. Offer to enable it — a state change requiring **explicit confirmation**:
   ```bash
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows update <flowId> --trigger on
   ```
3. After enabling (only on confirmation), trigger the flow.

## Step 5: Handle a failing response

If the trigger returns a **non-2xx** status, surface the **status and response body**, then offer to inspect the run:
- Offer to run the `get-flow-run` skill with the Run ID to see the failing block, reason, and status.

```
Trigger returned 500.
  Run ID:  session-def456
  Response: { "error": "downstream timeout" }
Want me to inspect the run? I can pull the per-block detail with get-flow-run for session-def456.
```

---

Read `references/flows-cli-baseline.md` for CLI prefixing, credential reuse, and error handling rules.

Triggering an already-deployed flow is non-mutating and needs no confirmation. Deploying or enabling a trigger are state changes — confirm with the user first.
