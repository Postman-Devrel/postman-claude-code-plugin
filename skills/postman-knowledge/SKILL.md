---
name: postman-knowledge
description: Postman concepts and MCP tool guidance. Loaded when working with Postman MCP tools to make better decisions about tool selection and workarounds.
user-invocable: false
---

# Postman Knowledge

Reference for Postman concepts and MCP tool selection. Use this context when working with Postman MCP tools to make better decisions.

## Core Concepts

- **Collection:** A group of API requests organized in folders. The primary unit of work in Postman. Contains requests, examples, tests, and documentation.
- **Environment:** Key-value pairs (variables) scoped to a context (dev, staging, prod). Used to swap base URLs, auth tokens, and config without changing requests.
- **Workspace:** Container for collections, environments, and specs. Can be personal, team, or public.
- **Spec (Spec Hub):** An OpenAPI or AsyncAPI definition stored in Postman. Can generate collections and stay synced.
- **Request:** A single API call definition (method, URL, headers, body, tests).
- **Response:** A saved example response for a request. Used by mock servers and documentation.
- **Folder:** A grouping within a collection, typically by resource (e.g., "Users", "Orders").
- **Tags:** Labels on collections for categorization and search.
- **Monitor:** A scheduled collection runner that checks API health.
- **Mock Server:** A fake API that serves example responses from a collection.

## Decision Guide

| Goal | Approach |
|------|----------|
| Push code changes to Postman | Create/update spec in Spec Hub, then sync to collection |
| Consume a Postman API | Read collection + generate client code |
| Find an API | Search workspace collections, then drill into details |
| Test an API | Run collection with `runCollection` |
| Create a fake API for frontend | Create mock server from collection with examples |
| Document an API | Analyze collection completeness, fill gaps, optionally publish |
| Audit API security | Run security checks against spec or collection |

## MCP Tool Selection

**Workspace operations:** `getWorkspaces`, `getWorkspace`, `createWorkspace`
**Collection CRUD:** `getCollections`, `getCollection`, `createCollection`, `putCollection`, `patchCollection`, `deleteCollection`
**Request/Response:** `getCollectionRequest`, `createCollectionRequest`, `updateCollectionRequest`, `getCollectionResponse`, `createCollectionResponse`, `updateCollectionResponse`
**Folder management:** `getCollectionFolder`, `createCollectionFolder`, `updateCollectionFolder`
**Spec Hub:** `getAllSpecs`, `getSpec`, `createSpec`, `getSpecDefinition`, `updateSpecFile`, `getSpecFiles`
**Sync:** `generateCollection`, `syncCollectionWithSpec`, `syncSpecWithCollection`
**Environments:** `getEnvironments`, `getEnvironment`, `createEnvironment`, `putEnvironment`
**Mocks:** `getMocks`, `getMock`, `createMock`, `publishMock`, `unpublishMock`
**Tests:** `runCollection`
**Docs:** `publishDocumentation`, `unpublishDocumentation`
**Search:** `searchPostmanElements` (public network only), `getTaggedEntities`
**User:** `getAuthenticatedUser`

See `mcp-limitations.md` in this skill folder for known limitations and workarounds.
