---
description: Generate typed client code from Postman collections. Reads your private APIs and writes production-ready code.
allowed-tools: Bash, Read, Write, Glob, Grep, mcp__postman__*
---

# Generate Client Code

Generate typed client code from Postman collections. Reads your private API definitions and writes production-ready code that matches your project's conventions.

## Prerequisites

The Postman MCP Server must be connected. If MCP tools aren't available, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."

## Workflow

### Step 1: Find the API

1. Call `getWorkspaces` to get the user's workspace ID. If multiple workspaces exist, ask which to use.
2. Call `getCollections` with the `workspace` parameter. Use the `name` filter if the user specified an API name.
3. If no results in private workspace, fall back to `searchPostmanElements` to search the public Postman network.
4. If multiple matches, list them and ask which one.
5. Call `getCollection` to get the full collection.
6. Call `getSpecDefinition` if a linked spec exists (richer type info).

### Step 2: Understand the API Shape

For the target collection:
1. Call `getCollectionFolder` for each folder to understand resource grouping
2. Call `getCollectionRequest` for each relevant endpoint to get:
   - HTTP method and URL
   - Request headers and auth
   - Request body schema
   - Path and query parameters
3. Call `getCollectionResponse` for each request to get:
   - Response status codes
   - Response body shapes (for typing)
   - Error response formats
4. Call `getEnvironment` to understand base URLs and variables
5. Call `getCodeGenerationInstructions` for any Postman-specific codegen guidance

### Step 3: Detect Project Language

If the user doesn't specify a language, detect from the project:
- `package.json` or `tsconfig.json` → TypeScript/JavaScript
- `requirements.txt` or `pyproject.toml` → Python
- `go.mod` → Go
- `Cargo.toml` → Rust
- `pom.xml` or `build.gradle` → Java
- `Gemfile` → Ruby

### Step 4: Generate Code

Generate a typed client class or module with:
- Method per endpoint with proper parameters
- Request/response types from collection schemas
- Authentication handling (from collection auth config)
- Error handling based on documented error responses
- Environment-based configuration (base URL from env vars)
- Pagination support if the API uses it

**Code conventions:**
- Match the project's existing style (imports, formatting, naming)
- Include JSDoc/docstrings from collection descriptions
- Use the project's HTTP library if one exists (axios, fetch, requests, etc.)
- Write to a sensible file path (e.g., `src/clients/<api-name>.ts`)

### Step 5: Present

```
Generated: src/clients/users-api.ts

  Endpoints covered:
    GET    /users         → getUsers(filters)
    GET    /users/{id}    → getUser(id)
    POST   /users         → createUser(data)
    PUT    /users/{id}    → updateUser(id, data)
    DELETE /users/{id}    → deleteUser(id)

  Types generated:
    User, CreateUserRequest, UpdateUserRequest,
    UserListResponse, ApiError

  Auth: Bearer token (from USERS_API_TOKEN env var)
  Base URL: from USERS_API_BASE_URL env var
```

## Error Handling

- **MCP not configured:** "Run `/postman:setup` to configure the Postman MCP Server."
- **Collection not found:** "No collection matching that name. Run `/postman:search` to find available APIs."
- **401 Unauthorized:** "Your Postman API key was rejected. Generate a new one at https://postman.postman.co/settings/me/api-keys and run `/postman:setup`."
- **Empty collection:** "This collection has no requests. Add endpoints in Postman or use `/postman:sync` to push a spec."
- **Language not detected:** Ask the user what language to generate.
