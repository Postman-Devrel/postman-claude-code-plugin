# Known MCP Limitations

These limitations are documented so they are handled correctly in all commands and workflows.

## searchPostmanElements is Public-Only

`searchPostmanElements` searches the PUBLIC Postman network only, not the user's private workspaces.

**Workaround:** For private content, use `getWorkspaces` + `getCollections` + `getCollection`. Use `searchPostmanElements` only as a fallback when searching for public APIs.

## generateCollection is Async

`generateCollection` returns HTTP 202 (accepted), not the collection directly.

**Workaround:** Poll `getGeneratedCollectionSpecs` or `getSpecCollections` for completion. Note: `getAsyncSpecTaskStatus` may return 403 on some plans; use the alternatives.

## syncCollectionWithSpec is Async and OpenAPI 3.0 Only

`syncCollectionWithSpec` returns HTTP 202 and only supports OpenAPI 3.0 specifications.

**Workaround for async:** Poll `getCollectionUpdatesTasks` for completion.

**Workaround for non-3.0 specs:** For Swagger 2.0 or OpenAPI 3.1 specs, use `updateSpecFile` to update the spec and regenerate the collection with `generateCollection`.

## createCollection Cannot Nest Folders

`createCollection` creates a flat collection. You cannot nest folders in a single call.

**Workaround:** Decompose the operation:
1. `createCollection` to create the collection
2. `createCollectionFolder` to add folders
3. `createCollectionRequest` to add requests to folders

## putCollection Auth Enum Lacks "noauth"

The `putCollection` auth type enum does not include "noauth" as a valid value.

**Workaround:** Endpoints that need no auth should inherit from collection-level settings or use a different auth type as a placeholder.

## createSpec Impractical for Large Specs

`createSpec` struggles with specs larger than ~50KB due to request size limits.

**Workaround:** For large APIs, parse the spec locally and create collection items directly using `createCollection` + `createCollectionFolder` + `createCollectionRequest` + `createCollectionResponse`.
