# Flows CLI Baseline

These rules apply to every Flows CLI skill.

- Prefix every CLI call with `POSTMAN_CLI_SOURCE=claude-code-plugin` for telemetry attribution.
- Reuse existing `postman login` / API key credentials. Do not trigger a second authentication.
- Surface CLI errors verbatim. Do not assert access the CLI does not grant.
- **CLI not installed:** "Postman CLI is not installed. Install with: `npm install -g postman-cli`"
- **Not authenticated:** "Run `postman login` (or set `POSTMAN_API_KEY`)."
