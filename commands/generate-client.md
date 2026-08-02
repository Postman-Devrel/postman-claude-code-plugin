---
description: Generate typed client code from a Postman collection. Reads your private APIs and writes production-ready client code that matches your project conventions.
allowed-tools: Bash, Read, Write, Glob, Grep, mcp__postman__searchPostmanElements, mcp__postman__getWorkspaces, mcp__postman__getCollections, mcp__postman__getCollection, mcp__postman__getCollectionFolder, mcp__postman__getCollectionRequest, mcp__postman__getCollectionResponse, mcp__postman__getEnvironment, mcp__postman__getSpecDefinition, mcp__postman__getCodeGenerationInstructions
---

# Generate Client Code

Generate typed client code from a Postman collection. Reads your private APIs and writes production-ready client code that matches your project's language and conventions.

This is the inverse of `/postman:generate-spec` (which authors an OpenAPI spec *from* your code): here the collection is the source of truth and code is the output.

## Prerequisites

The Postman MCP Server must be connected. If MCP tools aren't available, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."

This command's codegen tools (`getCodeGenerationInstructions`, the collection readers) require **Full** or **Code** MCP mode. This plugin defaults to Full mode, so it works out of the box; if the tools are missing, run `/postman:use-remote` (or unset `POSTMAN_MCP_MODE`) and restart Claude Code.

## Workflow

### Step 1: Find the API

1. Call `searchPostmanElements` with the API name and `entityType: collections`. Set `ownership` based on the user's intent:
   - `ownership: organization` (default) for the user's org resources. To restrict to the trusted Private API Network, add `filters: {"$and":[{"privateNetwork":{"$eq":true}}]}`.
   - `ownership: external` for third-party public APIs.
   - `ownership: all` to search everywhere.
2. If results are sparse, broaden the search (widen `ownership`, relax filters) or fall back to `getWorkspaces` + `getCollections` with the `workspace` parameter and `name` filter.
3. Match by name or ask the user which collection to generate code from.
4. Call `getCollection` (full model) to get the complete collection with all requests, bodies, and params.
5. Call `getSpecDefinition` if a linked spec exists (richer type information).
6. Call `getCodeGenerationInstructions` for the MCP server's recommended codegen workflow.

### Step 2: Understand the API Shape

For the target collection:
1. Call `getCollectionFolder` for each folder to understand resource grouping.
2. Call `getCollectionRequest` for each relevant endpoint to get:
   - HTTP method and URL
   - Request headers and auth requirements
   - Request body schema
   - Path and query parameters
3. Call `getCollectionResponse` for each request to get:
   - Response status codes
   - Response body shapes (for typing)
   - Error response formats
4. Call `getEnvironment` to understand base URLs and variables.

### Step 3: Detect Project Language

If the user doesn't specify a language, detect it from the project:

| File | Language |
|------|----------|
| `package.json` + `tsconfig.json` | TypeScript |
| `package.json` (no tsconfig) | JavaScript |
| `requirements.txt` or `pyproject.toml` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml` or `build.gradle` | Java |
| `*.csproj` | C# |
| `Gemfile` | Ruby |

### Step 4: Generate Code

Generate a client that includes:

- **Typed client class or module** with one method per endpoint
- **Request/response types** from the collection schemas and examples
- **Authentication handling** based on collection auth config (Bearer, API key, OAuth2)
- **Error handling** with typed error responses from documented error schemas
- **Environment-based configuration** (base URL from env vars)
- **Pagination support** if the API uses cursor or offset pagination

The generated code should:
- Match the project's existing conventions (imports, formatting, naming style)
- Include JSDoc, docstrings, or doc comments from collection descriptions
- Use the project's existing HTTP library if one is present (axios, fetch, requests, reqwest, etc.)
- Use proper camelCase/snake_case matching the target language conventions
- Handle query parameters, path parameters, headers, and request bodies correctly

### Step 5: Write and Present

Write the generated code to an appropriate location in the project:
- TypeScript/JavaScript: `src/clients/<api-name>.ts` or `src/lib/<api-name>.ts`
- Python: `src/clients/<api_name>.py` or `<package>/clients/<api_name>.py`
- Go: `pkg/clients/<apiname>.go` or `internal/clients/<apiname>.go`

Present a summary:

```
Generated: src/clients/users-api.ts

  Endpoints covered:
    GET    /users         -> getUsers(filters)
    GET    /users/{id}    -> getUser(id)
    POST   /users         -> createUser(data)
    PUT    /users/{id}    -> updateUser(id, data)
    DELETE /users/{id}    -> deleteUser(id)

  Types generated:
    User, CreateUserRequest, UpdateUserRequest,
    UserListResponse, ApiError

  Auth: Bearer token (from USERS_API_TOKEN env var)
  Base URL: from USERS_API_BASE_URL env var
```

## Error Handling

| Error | Response |
|-------|----------|
| MCP not configured | "Run `/postman:setup` to configure the Postman MCP Server." |
| Codegen tools missing (wrong mode) | "Client generation requires Full or Code MCP mode. Run `/postman:use-remote` (or unset `POSTMAN_MCP_MODE`) and restart Claude Code." |
| Collection not found | "I didn't find a collection matching that name. Run `/postman:search` to see what's available." |
| No requests in collection | "This collection is empty. Add requests in Postman first, or use `/postman:sync` to create from a spec." |
| Can't detect language | "I can't detect the project language. What language should I generate the client in?" |
| Missing auth config | "This collection doesn't specify an auth method. I'll generate the client without auth. You can add it later." |
| Spec not available | "No linked spec found. I'll generate types from the collection's saved examples and request bodies." |
