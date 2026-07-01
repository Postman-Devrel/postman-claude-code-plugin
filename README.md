<p align="center">
  <img src="https://voyager.postman.com/logo/postman-logo-orange.svg" alt="Postman" width="320">
</p>

# Postman Plugin for Claude Code

The Postman Plugin provides a single, simple install for Claude Code. It provides full API lifecycle management, and best practices when working with Postman APIs. 

## What's included:
- Commands for setting up the Postman MCP Server (no more manual installs!), working with Collections, Tests, Mock Servers, and generating code and documentation from Collections
- Skills for API discovery and client code generation, OpenAPI spec generation, Postman CLI workflows, and API best practices
- Agent for reviewing API production readiness and providing recommendations based on the <a href="https://www.postman.com/ai/90-day-ai-readiness-playbook/">Postman API Readiness Guide</a>.

## Installation

Clone the repo and load it as a local plugin:

```bash
git clone https://github.com/Postman-Devrel/postman-claude-code-plugin.git
```

Then start Claude Code with the plugin loaded:

```bash
cd your-api-project/
claude --plugin-dir /path/to/postman-claude-code-plugin
```

## Quick Start

1. Start Claude Code with the plugin:
```bash
claude --plugin-dir /path/to/postman-claude-code-plugin
```

2. Run setup:
```
/postman:setup
```

3. Authenticate when prompted — **OAuth (recommended)**, which opens a browser sign-in with no key copying, or an API key:
```bash
export POSTMAN_API_KEY=PMAK-your-key-here
```
If you use an API key, add it to your shell profile (`~/.zshrc` or `~/.bashrc`) to persist across sessions. Get one at [go.postman.co/settings/me/api-keys](https://go.postman.co/settings/me/api-keys).

That's it. The plugin auto-configures the Postman MCP Server, verifies your connection, and lists your workspaces. You're ready to go.

## Commands

| Command | What It Does |
|---------|-------------|
| `/postman:setup` | Configure API key, verify connection, select workspace |
| `/postman:sync` | Create or update Postman collections from OpenAPI specs |
| `/postman:search` | Find APIs across your org's resources, your workspaces, and the public Postman network |
| `/postman:context` | Fetch real API definitions, generate and maintain typed client code |
| `/postman:test` | Run collection tests, diagnose failures, suggest fixes |
| `/postman:mock` | Create mock servers for frontend development |
| `/postman:docs` | Generate, improve, and publish API documentation |
| `/postman:security` | Security audit against OWASP API Top 10 |

## What You Can Do

### Sync your API to Postman
```
"Sync my OpenAPI spec with Postman"
→ Detects local spec, creates/updates collection, sets up environment
```

### Generate client code from private APIs
```
"Generate a TypeScript client for the payments API"
→ Reads your Postman collection, detects project language, writes typed code
```

### Search across your workspace
```
"Is there an endpoint that returns user emails?"
→ Searches across your org's collections, drills into endpoint details, shows response shapes
```

### Run API tests
```
"Run the tests for my User API collection"
→ Executes collection, parses results, diagnoses failures, suggests code fixes
```

### Create mock servers
```
"Create a mock for frontend development"
→ Generates missing examples, creates mock, provides integration config
```

### Audit API security
```
"Run a security audit on my API"
→ 20+ checks including OWASP Top 10, severity scoring, remediation guidance
```

### Check if your API is agent-ready
```
"Is my API ready for AI agents?"
→ 48 checks across 8 pillars, scored 0-100, prioritized fix recommendations
```

## Natural Language Routing

You don't need to remember command names. Claude matches your intent to the right command or skill natively:

- "Sync my collection" runs `/postman:sync`
- "Check for vulnerabilities" runs `/postman:security`
- "Is my API agent-ready?" triggers the readiness analyzer

## API Readiness Analyzer

The built-in readiness analyzer evaluates APIs for AI agent compatibility across 8 pillars:

| Pillar | What It Checks |
|--------|---------------|
| Metadata | operationIds, summaries, descriptions, tags |
| Errors | Error schemas, codes, retry guidance |
| Introspection | Parameter types, required fields, examples |
| Naming | Consistent casing, RESTful paths |
| Predictability | Response schemas, pagination, date formats |
| Documentation | Auth docs, rate limits |
| Performance | Rate limit headers, caching, bulk endpoints |
| Discoverability | OpenAPI version, server URLs |

**70%+ with no critical failures = Agent-Ready.**

## Requirements

- Claude Code v1.0.33+
- A Postman account — authenticate via OAuth during `/postman:setup`, or set a `POSTMAN_API_KEY` environment variable
- No Python, Node, or other runtime dependencies

## How It Works

The plugin bundles a `.mcp.json` file that auto-configures the [Postman MCP Server](https://github.com/postmanlabs/postman-mcp-server) when installed. All commands communicate with Postman through MCP tools. No scripts, no dependencies, pure MCP.

By default the plugin connects to the full Postman MCP Server (100+ tools). Recent Claude Code versions load MCP tool schemas on demand, so the full server adds little context overhead. If you're on an older client or want a lighter session, set `POSTMAN_MCP_MODE` before starting Claude Code to pick a smaller server mode:

```bash
export POSTMAN_MCP_MODE=minimal   # ~42 CRUD tools; code-generation (context) tools unavailable
export POSTMAN_MCP_MODE=code      # ~24 read-only tools for API discovery and client code generation
```

## License

Apache-2.0

## See Also

- [Postman Plugin for Cursor](https://github.com/Postman-Devrel/cursor-postman-plugin) - Same capabilities, adapted for Cursor IDE
- [Postman Agent Skills](https://github.com/Postman-Devrel/agent-skills) - Portable skills for any skills.sh-compatible agent
- [Postman Cursor Rules](https://github.com/Postman-Devrel/postman-cursor-rules) - Lightweight MCP config + rules for Cursor

## Links

- [Postman MCP Server Docs](https://learning.postman.com/docs/developer/postman-mcp-server/)
- [Get a Postman API Key](https://go.postman.co/settings/me/api-keys)
- [Postman Status](https://status.postman.com)
