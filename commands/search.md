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

1. Call `searchPostmanElementsInPrivateNetwork` with the user's query. This searches the organization's private API network and is the **primary** search path.
2. If private network results are sparse or private network search is not available, broaden the search:
   - Call `getWorkspaces` to get the user's workspace ID. If multiple workspaces exist, ask which to use. Then use `getCollections` with the `workspace` parameter. Use the `name` filter to narrow results.
   - Call `getTaggedEntities` to find collections by tag.
3. If the user is looking for a public/third-party API (e.g., Stripe, GitHub, Twilio), call `searchPostmanElementsInPublicNetwork` with the user's query.

**Important:** Default to `searchPostmanElementsInPrivateNetwork` for trusted APIs in user's organisation. Only use `searchPostmanElementsInPublicNetwork` when the user explicitly wants public/third-party APIs or private search returns no results.

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
- **No results:** "Nothing matched in your private API network. Try different keywords, browse in user's workspaces, or search the public Postman network."
- **401 Unauthorized:** "Your Postman API key was rejected. Generate a new one at https://go.postman.co/settings/me/api-keys and run `/postman:setup`."
- **Too many results:** Ask the user to be more specific. Suggest filtering by workspace or using tags.
