---
description: Create Postman mock servers for frontend development. Generates missing examples, provides integration config.
allowed-tools: Bash, Read, Write, Glob, Grep, mcp__postman__*
---

# Create Mock Servers

Spin up a Postman mock server from a collection or spec. Get a working mock URL for frontend development, integration testing, or demos.

## Prerequisites

The Postman MCP Server must be connected. If MCP tools aren't available, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."

## Workflow

### Step 1: Find the Source

Call `getWorkspaces` to get the user's workspace ID. If multiple workspaces exist, ask which to use.

**From existing collection:**
- Call `getCollections` with the `workspace` parameter
- Select the target collection

**From local spec:**
- Find OpenAPI spec in the project
- Import it first:
  1. Call `createSpec` with `workspaceId`, `name`, `type`, and `files`
  2. Call `generateCollection`. **Async (HTTP 202).** Poll `getGeneratedCollectionSpecs` or `getSpecCollections` for completion. Note: `getAsyncSpecTaskStatus` may return 403 on some plans.

### Step 2: Check for Examples

Mock servers serve example responses. Call `getCollection` and check if requests have saved responses.

If examples are missing:
```
Your collection doesn't have response examples. Mock servers need
these to know what to return.

Generating realistic examples from your schemas...
```

For each request without examples:
1. Call `getCollectionRequest` to get the schema
2. Generate a realistic example response from the schema
3. Call `createCollectionResponse` to save the example

### Step 3: Check for Existing Mocks

Before creating a new mock, call `getMocks` to check if one already exists for this collection. If found, call `getMock` to get its URL and present it. Only create a new mock if none exists or the user explicitly wants a new one.

### Step 4: Create Mock Server

Call `createMock` with:
- Workspace ID
- Collection UID in `ownerId-collectionId` format (from `getCollection` response's `uid` field)
- Environment ID (if applicable)
- Name: `<api-name> Mock`
- Private: false (or true if user prefers)

### Step 5: Present Mock URL

```
Mock server created: "Pet Store API Mock"
  URL: https://<mock-id>.mock.pstmn.io
  Status: Active

  Try it:
    curl https://<mock-id>.mock.pstmn.io/pets
    curl https://<mock-id>.mock.pstmn.io/pets/1
    curl -X POST https://<mock-id>.mock.pstmn.io/pets -d '{"name":"Buddy"}'

  The mock serves example responses from your collection.
  Update examples in Postman to change mock behavior.
```

### Step 6: Integration

```
Quick integration:

  # Add to your project .env
  API_BASE_URL=https://<mock-id>.mock.pstmn.io

  # Or in your frontend config
  const API_URL = process.env.API_BASE_URL || 'https://<mock-id>.mock.pstmn.io';
```

### Step 7: Publish (optional)

If the user wants the mock publicly accessible:
- Call `publishMock` to make it available without authentication
- Useful for demos, hackathons, or public documentation
- Call `unpublishMock` to make it private again

## Error Handling

- **MCP not configured:** "Run `/postman:setup` to configure the Postman MCP Server."
- **No examples in collection:** Auto-generate from schemas (Step 2). If no schemas either, ask the user to provide sample responses.
- **401 Unauthorized:** "Your Postman API key was rejected. Generate a new one at https://postman.postman.co/settings/me/api-keys and run `/postman:setup`."
- **MCP timeout:** Retry once. If it still fails, check https://status.postman.com for outages.
- **Plan limitations:** "Mock server creation may require a Postman Basic plan or higher for increased usage limits."
