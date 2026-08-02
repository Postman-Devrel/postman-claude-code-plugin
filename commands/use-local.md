---
description: Switch this plugin's Postman MCP Server to the LOCAL stdio package (npx @postman/postman-mcp-server@latest). Requires POSTMAN_API_KEY.
allowed-tools: Bash, Read, Write
---

# Use Local MCP Server

Point this plugin at the **local** Postman MCP Server — the stdio package run via `npx @postman/postman-mcp-server@latest` — instead of Postman's hosted remote server. This rewrites the plugin's own `.mcp.json` in place, changing only the transport (remote → local). The local server authenticates with a `POSTMAN_API_KEY` read from your environment (there is no OAuth for the local package).

Switch back to the hosted server at any time with `/postman:use-remote`.

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

### Step 2: Verify the API key

The local server reads a Postman API key from the environment. Check it:

```bash
if [ -n "$POSTMAN_API_KEY" ]; then echo "POSTMAN_API_KEY is set"; else echo "POSTMAN_API_KEY is NOT set"; fi
```

If it is **not** set, tell the user to run `export POSTMAN_API_KEY=PMAK-your-key-here` and add that line to `~/.zshrc` or `~/.bashrc` so it persists, then restart the shell before continuing. They can generate a key at https://go.postman.co/settings/me/api-keys. Never hardcode the key into the file — it is read from the environment.

### Step 3: Overwrite the target `.mcp.json`

Write exactly this content to the `FOUND:` path:

```json
{
  "mcpServers": {
    "postman": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@postman/postman-mcp-server@latest"],
      "env": {
        "POSTMAN_API_KEY": "${POSTMAN_API_KEY}"
      }
    }
  }
}
```

The `${POSTMAN_API_KEY}` reference is expanded by Claude Code from your environment (the same expansion the remote config uses for `${POSTMAN_MCP_MODE}`), and the spawned stdio process also inherits your shell environment. To preserve a specific toolset, add the matching mode flag to `args` (e.g. `--full`, `--code`, `--minimal`); with no mode flag the package runs its default toolset.

### Step 4: Confirm and restart

Print the new file content back to the user, confirm the switch (remote → local stdio), and tell them to **restart Claude Code** for the change to take effect. Remind them they can switch back to the hosted server at any time with `/postman:use-remote`.

## Error Handling

- **`.mcp.json` not found:** Ask the user for the path to the installed plugin's `.mcp.json`, or tell them to reinstall the plugin.
- **`POSTMAN_API_KEY` not set:** Walk through Step 2 — the local server cannot authenticate without it.
- **`npx` unavailable:** The local package needs Node.js. Tell the user to install Node, or switch back with `/postman:use-remote` (the hosted server needs no local runtime).
