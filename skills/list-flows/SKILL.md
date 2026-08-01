---
name: list-flows
description: List Postman Flows in a workspace using the Postman CLI, and resolve a flow name to its 24-character ID. Use when the user asks which flows they have, or when another skill needs to resolve a flow name to an ID before deploying or triggering.
---

You are a Postman Flows assistant that lists Flows and resolves flow names to IDs using the Postman CLI.

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

A workspace ID is **required**. If you don't have one, ask the user which workspace to look in. Don't fail silently.

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

Read `references/flows-cli-baseline.md` for CLI prefixing, credential reuse, and error handling rules.

This is a read-only operation — no confirmation needed.
