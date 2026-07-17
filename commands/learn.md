---
description: Search the Postman Learning Center for how-to guidance, feature explanations, and suggested workflows. Use for "how do I..." questions about the Postman product.
allowed-tools: Read, mcp__postman__searchLearningCenter, mcp__postman__getEnabledTools
---

# Learn Postman

Answer "how do I..." questions about the Postman product by searching the official Postman Learning Center (https://learning.postman.com). Explain features, walk through workflows, and cite authoritative sources.

Use this to learn *about Postman itself* — not to search the user's own collections, workspaces, or specs (that's `/postman:search`).

## Prerequisites

This command uses `searchLearningCenter`, which is only exposed when the Postman MCP Server runs in **Full mode** (`POSTMAN_MCP_MODE=mcp`, the default). It is **not** available in `minimal` or `code` mode.

- If MCP tools aren't available at all, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."
- If `searchLearningCenter` specifically is missing, call `getEnabledTools` to confirm the active tool set, then tell the user: "Searching the Learning Center requires Full mode. Unset `POSTMAN_MCP_MODE` (or set it to `mcp`) and restart Claude Code."

## Workflow

### Step 1: Search

Call `searchLearningCenter` with a focused `query` derived from the user's question. Prefer the product vocabulary from `postman-knowledge` (mock server, environment, monitor, collection variable, etc.) over the user's exact phrasing.

- Turn a broad request into a specific query — "how to create a mock server", "write a test script", "set a collection variable", "schedule a monitor".
- If results are thin or off-target, refine: try a different feature term, split a multi-part question into separate searches, or broaden a narrow query.

### Step 2: Synthesize

Read the returned passages and compose a direct answer to the user's question. Do not just dump raw results.

- Lead with the answer or the concrete steps.
- Keep steps in the order the user would perform them.
- If the docs reveal a better or officially recommended workflow than what the user asked, surface it.
- Always cite the source URLs the tool returns so the user can read more.

### Step 3: Connect to the Plugin

When a workflow maps to a plugin command, point the user there so they can act immediately:

- Creating/updating collections from a spec → `/postman:sync`
- Finding APIs in their org or the public network → `/postman:search`
- Running collection tests → `/postman:test`
- Creating mock servers → `/postman:mock`
- Generating or publishing docs → `/postman:docs`
- Security auditing → `/postman:security`

## Output

```
To create a mock server in Postman:

  1. Open the collection you want to mock (it needs saved example responses).
  2. Select the collection → "Mock collection".
  3. Name the mock, pick an environment, and choose visibility.
  4. Postman returns a mock URL that serves your examples.

  Mock servers read from saved examples, so add examples first if you
  have none — the plugin can do this for you via /postman:mock.

  Source: https://learning.postman.com/docs/design-apis/mock-apis/set-up-mock-servers/
```

## Error Handling

- **MCP not configured:** "Run `/postman:setup` to configure the Postman MCP Server."
- **Tool unavailable (wrong mode):** Confirm with `getEnabledTools`, then: "Searching the Learning Center requires Full mode. Unset `POSTMAN_MCP_MODE` (or set it to `mcp`) and restart Claude Code."
- **401 Unauthorized:** "Your Postman API key was rejected. Generate a new one at https://go.postman.co/settings/me/api-keys and run `/postman:setup`."
- **No results:** "Nothing matched in the Learning Center. Try rephrasing with the Postman feature name, or ask about a more specific step."
