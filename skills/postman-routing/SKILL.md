---
name: postman-routing
description: Automatically routes Postman and API-related requests to the correct command. Use when user mentions APIs, collections, specs, testing, mocks, docs, security, or Postman.
user-invocable: false
---

# Postman Command Routing

When the user's request involves Postman or APIs, route to the appropriate command. Always prefer commands over raw MCP tool calls. Commands provide structured workflows, async handling, error diagnosis, and formatted output.

## Routing Table

| User Intent | Command | Why |
|-------------|---------|-----|
| Import a spec, push spec to Postman, create collection from spec | `/postman:sync` | Creates spec + collection + environment, handles async polling |
| Sync collection, update collection, keep in sync, push changes | `/postman:sync` | Full sync workflow with change reporting |
| Generate client code, SDK, wrapper, consume an API | `/postman:codegen` | Reads collection shape, detects language, writes typed code |
| Find API, search endpoints, what's available, is there an API for | `/postman:search` | Searches private workspace first, drills into details |
| Run tests, check if tests pass, validate API | `/postman:test` | Runs collection, parses results, diagnoses failures, suggests fixes |
| Create mock server, fake API, mock for frontend | `/postman:mock` | Checks for examples, generates missing ones, provides integration config |
| Generate docs, improve documentation, publish docs | `/postman:docs` | Analyzes completeness, fills gaps, can publish to Postman |
| Security audit, check for vulnerabilities, OWASP | `/postman:security` | 20+ security checks with severity scoring and remediation |
| Set up Postman, configure API key, first-time setup | `/postman:setup` | Guided setup with workspace verification |
| Is my API agent-ready?, scan my API, analyze my spec | **readiness-analyzer agent** | 48 checks across 8 pillars, scoring and fix recommendations |

## Routing Rules

1. **Specific commands take priority.** If the intent clearly maps to one command, use it.
2. **Agent-readiness questions go to the agent.** Phrases like "agent-ready", "scan my API", "analyze my spec for AI" trigger the readiness-analyzer agent.
3. **Ambiguous requests get clarified.** If you can't determine intent, ask: "I can sync collections, generate client code, search for APIs, run tests, create mocks, generate docs, or audit security. What do you need?"
4. **Multi-step requests chain commands.** "Import my spec and run tests" = `/postman:sync` then `/postman:test`.

## When to Use Raw MCP Tools

Only use `mcp__postman__*` tools directly when:
- Making a single, targeted update (e.g., updating one request's body)
- The user explicitly asks to call a specific MCP tool
- The task doesn't match any command workflow
