---
description: Sync Postman collections with your API code. Create collections from specs, push updates, keep everything in sync.
allowed-tools: Bash, Read, Write, Glob, Grep, mcp__postman__*
---

# Sync Collections

Keep Postman collections in sync with your API code. Create new collections from OpenAPI specs, update existing ones when specs change, or push manual endpoint changes.

## Prerequisites

The Postman MCP Server must be connected. If MCP tools aren't available, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."

## Workflow

### Step 1: Understand What Changed

Detect or ask:
- Is there a local OpenAPI spec? Search for `**/openapi.{json,yaml,yml}`, `**/swagger.{json,yaml,yml}`
- Did the user add/remove/modify endpoints?
- Is there an existing Postman collection to update, or do they need a new one?

### Step 2: Resolve Workspace

Call `getWorkspaces` to get the user's workspace ID. If multiple workspaces exist, ask which to use.

### Step 3: Find or Create the Collection

**If updating an existing collection:**
1. Call `getCollections` with the `workspace` parameter to list collections
2. Match by name or ask the user which collection
3. Call `getCollection` to get current state

**If creating a new collection from a spec:**
1. Read the local OpenAPI spec
2. Call `createSpec` with:
   - `workspaceId`: the workspace ID
   - `name`: from the spec's `info.title`
   - `type`: one of `OPENAPI:2.0`, `OPENAPI:3.0`, `OPENAPI:3.1`, `ASYNCAPI:2.0`
   - `files`: array of `{path, content}` objects
3. Call `generateCollection` from the spec. **This is async (HTTP 202).** Poll `getAsyncSpecTaskStatus` or `getGeneratedCollectionSpecs` until complete.
4. Call `createEnvironment` with variables extracted from the spec:
   - `base_url` from `servers[0].url`
   - Auth variables from `securitySchemes` (mark as `secret`)
   - Common path parameters

### Step 4: Sync

**Spec to Collection (most common):**
1. Call `createSpec` or `updateSpecFile` with local spec content
2. Call `syncCollectionWithSpec` to update the collection. **Async (HTTP 202).** Poll `getCollectionUpdatesTasks` for completion.
3. **Note:** `syncCollectionWithSpec` only supports OpenAPI 3.0. For Swagger 2.0 or OpenAPI 3.1, use `updateSpecFile` and regenerate the collection.
4. Report what changed

**Collection to Spec (reverse sync):**
1. Call `syncSpecWithCollection` to update the spec from collection changes
2. Write the updated spec back to the local file

**Manual updates (no spec):**
For individual endpoint changes:
1. `createCollectionRequest` to add new endpoints
2. `updateCollectionRequest` to modify existing ones
3. `createCollectionFolder` to organize by resource
4. `createCollectionResponse` to add example responses

### Step 5: Confirm

```
Collection synced: "Pet Store API" (15 requests)
  Added:    POST /pets/{id}/vaccinations
  Updated:  GET /pets — added 'breed' filter parameter
  Removed:  (none)

  Environment: "Pet Store - Development" updated
  Spec Hub: petstore-v3.1.0 pushed
```

## Error Handling

- **MCP not configured:** "Run `/postman:setup` to configure the Postman MCP Server."
- **MCP timeout:** Retry once. If `generateCollection` or `syncCollectionWithSpec` times out, the spec may be too large. Suggest breaking it into smaller specs by domain.
- **401 Unauthorized:** "Your Postman API key was rejected. Generate a new one at https://postman.postman.co/settings/me/api-keys and run `/postman:setup`."
- **Invalid spec:** Report specific parse errors with line numbers. Offer to fix common YAML/JSON syntax issues.
- **Async operation stuck:** If polling shows no progress after 30 seconds, inform the user and suggest checking the Postman app directly.
- **Plan limitations:** "Workspace creation may be limited on free plans. Using your default workspace instead."
