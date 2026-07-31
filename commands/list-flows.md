---
description: List Postman Flows in a workspace and resolve a flow name to its 24-character ID
allowed-tools: Bash, Read
---

List Postman Flows in a workspace using the Postman CLI. Follow the `list-flows` skill.

## Inputs (from the user's message)
- The workspace ID (ask if unknown)
- Optionally a name/pattern to filter by

## Steps
1. Ensure you have a workspace ID; ask which workspace if not.
2. Run:
   ```bash
   POSTMAN_CLI_SOURCE=claude-code-plugin postman flows list --workspace <workspaceId>
   ```
   Narrow with `--filter "<name>"` when resolving a specific flow; use `--sort name` / `--paginate` as needed.
3. Report flow **names + IDs** (and recent status where shown). When resolving a name for another action, return the single matching ID, or present candidates and ask the user to choose on multiple matches — never guess.

Read-only: no confirmation needed. Prefix CLI calls with `POSTMAN_CLI_SOURCE=claude-code-plugin`. Reuse existing `postman login` credentials.
