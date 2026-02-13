---
description: Set up Postman MCP Server. Configure API key, verify connection, select workspace.
allowed-tools: mcp__postman__*
---

# First-Run Configuration

Walk the user through Postman setup for Claude Code. Validate everything works before they use other commands.

## Workflow

### Step 1: Check MCP Connection

Verify the Postman MCP Server is available by calling `getAuthenticatedUser`.

**If it works:** Skip to Step 3 (workspace verification).

**If it fails or tools aren't available:** Proceed to Step 2.

### Step 2: Configure API Key

```
Let's set up Postman for Claude Code.

1. Go to: https://postman.postman.co/settings/me/api-keys
2. Click "Generate API Key"
3. Name it "Claude Code"
4. Copy the key (starts with PMAK-)

Then set it as an environment variable:

  export POSTMAN_API_KEY=PMAK-your-key-here

Add it to your shell profile (~/.zshrc or ~/.bashrc) to persist across sessions.
```

Wait for the user to confirm they've set the key. Then verify with `getAuthenticatedUser`.

**If 401:** "API key was rejected. Check for extra spaces or generate a new one at https://postman.postman.co/settings/me/api-keys"

**If timeout:** "Can't reach the Postman MCP Server. Check your network and https://status.postman.com"

### Step 3: Workspace Verification

After successful connection:

1. Call `getWorkspaces` to list workspaces
2. Call `getCollections` with the first workspace ID to count collections
3. Call `getAllSpecs` with the workspace ID to count specs

Present:
```
Connected as: <user name>

Your workspaces:
  - My Workspace (personal) — 12 collections, 3 specs
  - Team APIs (team) — 8 collections, 5 specs

You're all set.
```

If workspace is empty:
```
Your workspace is empty. You can:
  /postman:sync     — Push a local OpenAPI spec to Postman
  /postman:search   — Search the public Postman API Network
```

### Step 4: Suggest First Command

Based on what the user has:

**Has collections:**
```
Try one of these:
  /postman:search   — Find APIs across your workspace
  /postman:test     — Run collection tests
  /postman:codegen  — Generate client code from a collection
```

**Has specs but no collections:**
```
Try this:
  /postman:sync — Generate a collection from one of your specs
```

**Empty workspace:**
```
Try this:
  /postman:sync — Import an OpenAPI spec from your project
```

## Error Handling

- **MCP tools not available:** "The Postman MCP Server isn't loaded. Make sure the plugin is installed and restart Claude Code."
- **API key not set:** Walk through Step 2 above.
- **401 Unauthorized:** "Your API key was rejected. Generate a new one at https://postman.postman.co/settings/me/api-keys"
- **Network timeout:** "Can't reach the Postman MCP Server. Check your network and https://status.postman.com for outages."
- **Plan limitations:** "Some features (team workspaces, monitors) require a paid Postman plan. Core commands work on all plans."
