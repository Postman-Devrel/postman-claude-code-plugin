---
description: Switch this plugin's Postman MCP Server to the REMOTE hosted server (https://mcp.postman.com/mcp, full mode). Authenticates via OAuth.
allowed-tools: Bash, Read, Write
---

# Use Remote MCP Server

Point this plugin back at Postman's **remote** hosted MCP Server (`https://mcp.postman.com`, Full mode) instead of the local stdio package. This rewrites the plugin's own `.mcp.json` in place, changing only the transport (local → remote). The hosted server authenticates via OAuth — no API key required.

This is the plugin's default configuration. Switch to the local package at any time with `/postman:use-local`.

## Workflow

### Step 1: Locate this plugin's `.mcp.json`

The file to rewrite is the `.mcp.json` bundled with this plugin (it lives at the plugin's root, next to `.claude-plugin/`). Find it and show the current content:

```bash
for f in "$CLAUDE_PLUGIN_ROOT/.mcp.json" "$HOME"/.claude/plugins/*/.mcp.json "$HOME"/.claude/plugins/*/*/.mcp.json; do
  [ -f "$f" ] || continue
  if grep -q '"postman"' "$f"; then echo "FOUND: $f"; echo "--- current content ---"; cat "$f"; echo; fi
done
```

Use the `FOUND:` path as the target file to edit. If nothing is found, stop and ask the user for the path to the installed plugin's `.mcp.json`.

### Step 2: Overwrite the target `.mcp.json`

Write exactly this content to the `FOUND:` path. This is the plugin's canonical remote form — Full mode (`https://mcp.postman.com/mcp`) with `X-Source` attribution headers:

```json
{
  "mcpServers": {
    "postman": {
      "type": "http",
      "url": "https://mcp.postman.com/${POSTMAN_MCP_MODE:-mcp}",
      "headers": {
        "X-Source": "claude-code-plugin",
        "X-Plugin-Version": "1.2.0",
        "User-Agent": "postman-claude-code-plugin/1.2.0"
      }
    }
  }
}
```

The `${POSTMAN_MCP_MODE:-mcp}` expansion defaults to `/mcp` (Full mode, 100+ tools) and honors a `POSTMAN_MCP_MODE` environment variable if the user wants a lighter toolset (`minimal`, `code`). Full mode is required by commands like `/postman:learn` (its `searchLearningCenter` tool is absent in `minimal` and `code` modes). Keep the `X-Source` / version headers intact so remote traffic stays attributed to this plugin.

### Step 3: Confirm and restart

Print the new file content back to the user, confirm the switch (local → remote hosted server), and tell them to **restart Claude Code** for the change to take effect. On first use, run `/postman:setup` to complete the Postman OAuth login (no API key needed). Remind them they can switch to the local package at any time with `/postman:use-local`.

## Error Handling

- **`.mcp.json` not found:** Ask the user for the path to the installed plugin's `.mcp.json`, or tell them to reinstall the plugin.
- **Connection fails after switching:** Run `/postman:setup` to (re)authenticate via OAuth against the hosted server.
- **401 Unauthorized:** "Your Postman session was rejected. Run `/postman:setup` to re-authenticate via OAuth."
