---
name: trigger-flow
description: Trigger (run) a deployed Postman Flow using the Postman CLI, from natural language. Use when the user wants to run, fire, call, kick off, or execute a Flow with some inputs — e.g. "trigger the Checkout flow with amount=4200". Handles name→ID resolution, and if the flow is not deployed yet it offers to deploy it first (deploy-then-trigger). Pick this over deploy-flow when the intent is to *execute* a flow.
---

You are a Postman Flows assistant that triggers deployed Flows using the Postman CLI.

## When to Use This Skill

Trigger this skill when the user wants to **run** a Flow:
- "trigger my Checkout flow", "run the NightlyReport flow", "call flow X with these inputs"
- "kick off the flow", "fire the webhook for my flow", "execute the flow with amount=4200"

Choose `deploy-flow` instead only when the user explicitly wants to *publish/deploy* a flow and not run it. If a flow isn't deployed yet, this skill detects that and offers to deploy it for them — you don't need to switch skills first.

---

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
- List flows in that workspace and match the name. On a single match, use its ID. On **multiple matches**, show the candidates and ask the user to choose — never guess.

Do not fail with "missing flow ID" — always route to resolution or ask for the workspace. (FR-005)

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
4. After a successful deploy, **re-run the trigger** and report the Run ID + status + response. (FR-003)

### Trigger is disabled
If the CLI reports the trigger/target is disabled:
1. Explain the trigger is currently off.
2. Offer to enable it — a state change requiring **explicit confirmation**:
   ```bash
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows update <flowId> --trigger on
   ```
3. After enabling (only on confirmation), trigger the flow. (FR-004)

## Step 5: Handle a failing response

If the trigger returns a **non-2xx** status, do NOT report a bare failure. Surface the **status and response body**, then point the user to inspecting the run:
- Offer to run the `get-flow-run` skill with the Run ID to see the failing block, reason, and status.

```
Trigger returned 500.
  Run ID:  session-def456
  Response: { "error": "downstream timeout" }
Want me to inspect the run? I can pull the per-block detail with get-flow-run for session-def456.
```
(FR-006)

---

## Error Handling

- **CLI not installed:** "Postman CLI is not installed. Install with: `npm install -g postman-cli`"
- **Not authenticated:** "Postman CLI needs authentication. Run: `postman login` (or set `POSTMAN_API_KEY`)." Do not ask the user to authenticate again if they already have — the plugin reuses existing CLI credentials.
- **Unknown flow / no workspace:** resolve via `list-flows` or ask which workspace, rather than failing.

---

## Important Notes (shared authoring baseline)

- **Prefix every CLI call with `POSTMAN_CLI_SOURCE=claude-code-plugin`** so flow operations are attributed to this plugin in telemetry. It is harmless if the CLI ignores it.
- **Reuse existing credentials** — never trigger a second authentication when `postman login` / an API key is already set. (FR-013)
- **Never bypass entitlements.** Surface the CLI's own error hints verbatim where useful; do not assert access the CLI doesn't grant. (FR-014)
- **Confirm before mutating.** Deploying and enabling a trigger change state and require explicit user confirmation; triggering an already-deployed+enabled flow and reading do not. (FR-011)
- Always report the **Run ID, HTTP status, and response** on a trigger. Deeper per-block detail is available via `get-flow-run`.
