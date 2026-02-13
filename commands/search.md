---
description: Discover APIs across your Postman workspaces. Ask natural language questions about available endpoints and capabilities.
allowed-tools: Read, Glob, Grep, mcp__postman__*
---

# Discover APIs

Answer natural language questions about available APIs across Postman workspaces. Find endpoints, check response shapes, and understand what's available.

## Prerequisites

The Postman MCP Server must be connected. If MCP tools aren't available, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."

## Workflow

### Step 1: Search

1. Call `getWorkspaces` to get the user's workspace ID. If multiple workspaces exist, ask which to use.
2. Call `getCollections` with the `workspace` parameter. Use the `name` filter to narrow results.
3. If results are sparse, broaden the search:
   - Call `getTaggedEntities` to find collections by tag
   - Call `getWorkspaces` to search across all workspaces
   - As a fallback for public APIs, call `searchPostmanElements` with the user's query

**Important:** `searchPostmanElements` only searches the PUBLIC Postman network, not private workspaces. Always search private workspace first using `getCollections`.

### Step 2: Drill Into Results

For each relevant hit:
1. Call `getCollection` to get the overview
2. Scan endpoint names and descriptions for relevance
3. Call `getCollectionRequest` for the most relevant endpoints
4. Call `getCollectionResponse` to show what data is available
5. Call `getSpecDefinition` if a linked spec exists for richer detail

### Step 3: Present

Format results as a clear answer to the user's question.

**When found:**
```
Yes, you can get a user's email via the API.

  Endpoint: GET /users/{id}
  Collection: "User Management API"
  Auth: Bearer token required

  Response includes:
    {
      "id": "usr_123",
      "email": "jane@example.com",
      "name": "Jane Smith",
      "role": "admin"
    }

  Want me to generate a client for this API? → /postman:codegen
```

**When not found:**
```
No endpoint returns user emails.

  Closest matches:
  - GET /users/{id}/profile — returns name, avatar (no email)
  - GET /users — list view doesn't include email

  The email field might require a different permission scope,
  or it may not be exposed via API yet.
```

**When multiple results:**
List relevant collections with endpoint counts, then ask which to explore further.

## Error Handling

- **MCP not configured:** "Run `/postman:setup` to configure the Postman MCP Server."
- **No results:** "Nothing matched in your workspace. Try different keywords, or search the public Postman network with broader terms."
- **401 Unauthorized:** "Your Postman API key was rejected. Generate a new one at https://postman.postman.co/settings/me/api-keys and run `/postman:setup`."
- **Too many results:** Ask the user to be more specific. Suggest filtering by workspace or using tags.
