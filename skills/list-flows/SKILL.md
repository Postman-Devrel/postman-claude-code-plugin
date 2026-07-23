---
name: list-flows
description: List Postman Flows in a workspace using the Postman CLI, and resolve a flow name to its 24-character ID. Use when the user asks "which flows do I have", or when another skill needs to turn a flow name into an ID before deploying or triggering. Read-only — no confirmation needed.
---

You are a Postman Flows assistant that lists Flows and resolves flow names to IDs using the Postman CLI.

## When to Use This Skill

Trigger this skill when:
- the user asks "what flows do I have", "list my flows", "show flows in workspace X"
- another skill (`trigger-flow`, `deploy-flow`, `get-flow-run`) needs to resolve a **flow name → 24-char ID**
- the user references a flow by name without giving an ID

This is a **read-only** operation — run it without asking for confirmation.

---

## The command this wraps

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows list --workspace <workspaceId> [options]
```

Options:
- `-w, --workspace <workspaceId>` — **required**
- `-f, --filter <pattern>` — filter by name (name prefix or regex)
- `-s, --sort <name|updated>` — sort criteria (default `updated`)
- `-p, --paginate` — page through all flows

## Step 1: Get the workspace ID

A workspace ID is **required**. If you don't have one, ask the user which workspace to look in. Don't fail silently. (FR-005 dependency)

## Step 2: List

```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows list --workspace 12345-67890-abcdef
```

Narrow with `--filter` when resolving a specific name:
```bash
POSTMAN_CLI_SOURCE=claude-code-plugin postman flows list --workspace 12345-67890-abcdef --filter "Checkout"
```

## Step 3: Report / resolve

- When the user asked to see their flows: report flow **names + IDs** (and recent status where shown).
- When resolving a name for another skill:
  - **Single match** → use that ID.
  - **Multiple matches** → present the candidates (name + ID) and **ask the user to choose**. Never guess. (Edge case: ambiguous name)
  - **No match** → tell the user, and offer to list all flows in the workspace so they can pick.

Example:
```
Flows in workspace 12345-67890-abcdef:
  1. Checkout        — 6f1a2b3c4d5e6f7a8b9c0d1e   (updated 2h ago)
  2. Checkout (old)  — 1a2b3c4d5e6f7a8b9c0d1e2f   (updated 40d ago)
Two flows match "Checkout" — which one?
```

---

## Error Handling

- **CLI not installed:** "Postman CLI is not installed. Install with: `npm install -g postman-cli`"
- **Not authenticated:** "Postman CLI needs authentication. Run: `postman login` (or set `POSTMAN_API_KEY`)." Don't re-authenticate if credentials already exist.
- **No workspace / invalid workspace:** ask for a valid workspace ID.

---

## Important Notes (shared authoring baseline)

- **Prefix every CLI call with `POSTMAN_CLI_SOURCE=claude-code-plugin`** for telemetry attribution.
- **Reuse existing credentials** — no second authentication. (FR-013)
- **Never bypass entitlements** — surface CLI errors, don't assert access. (FR-014)
- Read-only: listing needs **no** confirmation. (FR-011)
