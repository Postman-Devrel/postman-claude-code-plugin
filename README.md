# Postman Plugin for Claude Code

Official Postman plugin for Claude Code. Manage your entire API lifecycle without leaving your editor.

## Installation

```
/plugin install postman-skill
```

That's it. Type `/postman` and start managing your APIs.

## Features

- **Collection Management** - List, create, update, delete, and duplicate collections
- **Environment Management** - Manage variables across workspaces
- **Monitor Analysis** - Check API health and debug failures
- **Mock Servers** - Create and manage mock servers
- **Test Execution** - Run collection tests with environments
- **Agent-Readiness Analysis** - Grade your APIs for AI agent compatibility using Clara
- **Security Auditing** - Check APIs for security issues
- **Code Generation** - Generate code snippets in Python, JavaScript, Go, and more

## Usage

### Natural Language

```
/postman
Show me all my collections
```

```
/postman
Create a mock server for my Payment API
```

```
/postman
Is my API ready for AI agents?
```

### Common Operations

| Task | Example |
|------|---------|
| List collections | "Show my collections" |
| Create collection | "Create a collection called User API" |
| Run tests | "Run tests for Payment API with staging environment" |
| Check monitors | "How are my monitors doing?" |
| Create mock | "Create a mock server for Order API" |
| Analyze agent-readiness | "Is my API ready for AI agents?" |
| Security audit | "Check my API for security issues" |

## Setup

### Prerequisites

- Python 3.7+
- Postman API Key

### Configuration

1. Get your API key from [Postman Account Settings](https://go.postman.co/settings/me/api-keys)

2. Create a `.env` file:
```bash
cp .env.example .env
# Edit .env and add: POSTMAN_API_KEY=PMAK-your-key-here
```

## Agent-Readiness Analysis

This plugin includes Clara integration for grading APIs on AI agent compatibility.

Clara checks 8 pillars:
1. **Metadata** - operationIds, summaries, descriptions
2. **Errors** - Structured error responses
3. **Introspection** - Parameter types, examples
4. **Naming** - Consistent casing, RESTful paths
5. **Predictability** - Response schemas
6. **Documentation** - Auth docs, rate limits
7. **Performance** - Response times
8. **Discoverability** - Server URLs, spec accessibility

**Score 70%+ with no critical failures = Agent Ready**

## Documentation Intelligence

This plugin includes the **Postman Learning Center MCP** for documentation access. When you ask "how do I..." questions, Claude can pull actual Postman docs instead of guessing.

```
/postman
How do I set up OAuth 2.0 authentication?
```

The plugin queries `https://learning.postman.com/_mcp/server` for accurate, up-to-date documentation.

## Works With

This plugin complements:
- **[Postman Learning Center MCP](https://learning.postman.com/_mcp/server)** - Documentation and how-to guides (included)
- **[Postman's MCP Server](https://github.com/postmanlabs/postman-mcp-server)** - Live API operations

## License

MIT

## Author

Sterling Chin ([@sterlingchin](https://twitter.com/sterlingchin))
Developer Relations, Postman
