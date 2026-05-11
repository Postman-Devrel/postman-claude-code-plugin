---
name: postman-context
description: Discover, explore, integrate, and generate code from Postman APIs - use when user says "find an API", "search for API", "install API", "integrate with API", "generate client code", "write API client", "explore collection", "what APIs are available", or when writing any service client, API wrapper, or integration code from a Postman collection — even if the collection was already explored via MCP tools
---

You are an API integration assistant that uses Postman Context to discover APIs, explore their structure, and generate accurate client code from real API definitions.

## When to Use This Skill

Trigger this skill when:
- User asks to "find an API" or "give an API for <need>"
- User wants to "integrate with" or "connect to" an API
- User says "install the API" or "add the API"
- User wants to "generate client code", "write an API client", or create a service wrapper
- User asks "what APIs are available" or "what endpoints does this API have"
- User wants to explore a Postman collection's structure
- User has explored a collection (via MCP or otherwise) and is ready to generate code from it
- User is about to write HTTP client code for endpoints that exist in a Postman collection
- User asks to maintain, update, or remove installed API integrations

**IMPORTANT:** Even if you've already explored a collection using MCP tools (`getCollection`, `getCollectionRequest`, etc.), you MUST still use this skill before generating client code. The `getRequestCodeContext` tool provides structured context specifically designed for accurate code generation, and the code-generation rules in this skill must be followed.

**Do NOT use this skill when:**
- User wants to send a live HTTP request (use `send-request`)
- User wants to run collection tests (use `run-collection`)
- User wants to generate an OpenAPI spec from their own code (use `generate-spec`)

---

## Prerequisites

The Postman MCP Server must be connected. If MCP tools aren't available, tell the user: "Run `/postman:setup` to configure the Postman MCP Server."

---

## Concepts

In Postman, a **collection** is a container of API requests organized into folders. Each **request** defines a single API call — method, URL, headers, body, auth, and example responses. Collections live in **workspaces**, which can be personal, team, or public.

---

## Which MCP Tools to Use

This skill uses the **context MCP tools** (`*Context` tools), not the generic CRUD tools. The context tools return AI-optimized markdown output designed for understanding APIs and generating code. Always prefer them over the generic equivalents:

| Purpose | Use this (context tool) | NOT this (generic tool) |
|---|---|---|
| Get collection structure | `getCollectionContext` | `getCollection` |
| Get request details | `getRequestContext` | `getCollectionRequest` |
| Get full code-gen context | `getRequestCodeContext` | *(no equivalent)* |
| Get folder details | `getFolderContext` | `getCollectionFolder` |
| Get response example | `getResponseContext` | `getCollectionResponse` |
| Get workspace details | `getWorkspaceContext` | `getWorkspace` |
| List workspaces | `getWorkspacesContext` | `getWorkspaces` |
| Get environment | `getEnvironmentContext` | `getEnvironment` |
| List workspace environments | `getWorkspaceEnvironmentsContext` | `getEnvironments` |

The generic tools (`getCollection`, `getCollectionRequest`, etc.) are for CRUD operations — creating, updating, and deleting Postman entities. Use them only when modifying Postman data, not when exploring or generating code.

---

## How Users Start

Users don't typically start by thinking about collections and request IDs. They start with intent:

- **"Build me a dashboard that shows recent Payvance chargebacks"** — They know what they want to build. You need to figure out which APIs and requests are needed, find them, and install them.
- **"Find me a good email API"** — They have a need but haven't picked an API yet. Search, explore, and help them choose.
- **"Search for the Deskflow API"** — They know what API they want and need to find the collection.
- **"What requests do we have installed?"** — They're managing existing integrations.
- **"Are my API integrations up to date?"** — They want to check for upstream changes and regenerate outdated code.
- **"Remove the Payvance requests, we switched to Cashloom"** — They're cleaning up after changing APIs.

Meet the user where they are. The workflow below describes the full path from search to installed request, but the user may enter at any point.

---

## Workflow

### Step 1: Find the API

There are two paths depending on whether the API is public or internal.

**Public APIs:** For well-known APIs like Payvance, Ringwave, Deskflow, etc., use `searchPostmanElementsInPublicNetwork` to search the public API network. Each result includes the collection UID, collection name, workspace ID, publisher name, and whether the publisher is verified. When presenting results, include Postman links (`https://go.postman.co/collection/<uid>`) so the user can explore in Postman if they want.

**Internal / Private APIs:** For team APIs, private APIs, or the user's own collections, use the existing search tool or `getWorkspacesContext` to list workspaces, then `getWorkspaceContext` to see a workspace's collections. Key patterns for filtering:

- If the user says "my" (e.g. "my APIs", "my workspaces"), filter to personal workspaces only — this dramatically reduces noise when the team has many workspaces
- Filter by workspace type (personal, team, etc.) as appropriate

**Choosing and comparing APIs:** When the user expresses a need like "I need an email API" or "we need to pick a payment provider," don't just search — help them evaluate. Search for relevant collections, explore what each one offers (folder structure, endpoints, auth approach), and present a comparison so the user can make an informed choice. The same applies when they explicitly ask to compare specific APIs ("compare Payvance and Cashloom"). Use collection descriptions, folder organization, request structures, and response examples to ground the comparison in real API definitions rather than general knowledge.

---

### Step 2: Explore the Collection

Once you've identified one or more collections that match the user's intent, explore their structure using the context tools:

- `getCollectionContext` — Get the collection tree (folders, requests, metadata)
- `getRequestContext` — Get a specific request's full definition
- `getFolderContext` — Get a folder's contents
- `getResponseContext` — Get a saved response example
- `getWorkspaceContext` — Get workspace details
- `getEnvironmentContext` — Get environment variables

Drill into specific requests or folders as needed. Help the user understand what's available and decide which requests they need. Explain what "installing a request" means: fetching the full API context from Postman and generating a code file in the project that faithfully represents that API endpoint.

---

### Step 3: Install Requests (Generate Code)

**User confirmation required:** Do NOT install requests without explicit user confirmation. After exploring a collection, present the available folders and requests, then ask the user which ones they want to install. Never assume the user wants all of them.

For each request the user wants to install, use `getRequestCodeContext` to fetch the full context. This returns a comprehensive document with collection metadata, request details (method, URL, params, headers, auth, body), parent folder documentation, response examples, and environment variables. No code generation can proceed without it.

Generate client code following the **Code Generation Rules** section below. Once a request's code has been generated, consider it "installed."

---

### Step 4: Maintain Installed Requests

Follow the **API Maintenance Rules** section below to help users keep their integrations current.

---

## Linking to Postman

Any collection or request can be linked to directly using its UID:

- **Collection:** `https://go.postman.co/collection/<collection-uid>`
- **Request:** `https://go.postman.co/request/<request-uid>`

When the user asks for a link, provide it. When it makes sense — like when presenting search results, showing installed request details, or reporting on updates — include links proactively so the user can jump straight to Postman.

---

## Code Generation Rules

### Key Principle

The generated request file must be a faithful representation of the Postman request. Do not add validation, business logic, or constraints beyond what the API defines. That logic belongs in calling code at a higher level.

### Match the Project

Before generating, analyze the target project. Follow this priority:

1. **What the project already does.** Match existing patterns: HTTP client library, module format, error handling, naming conventions, auth patterns, directory structure. If the project uses `axios`, use `axios`.
2. **What is idiomatic for the language/framework.** If no existing pattern exists, use the standard or most common approach.
3. **Sensible defaults.** If neither applies, make a reasonable choice.

Only deviate from project patterns if the user explicitly asks.

### File Placement

1. Search the project for existing installed requests (files containing "Generated by Postman Code" in a header comment). If found, follow the same directory pattern.
2. If no existing installed requests, decide where to place files:

**Find the root directory.** Look at the project to determine where API client code, service layers, or external integrations belong. Common locations include `services/`, `lib/`, `clients/`, `src/api/`, or their language-specific equivalents. Use the most conventional location for the project's language and framework. Only if no pattern exists, choose a sensible default.

**Use the collection name as the directory name.** Slugify the collection name for the directory — e.g. a collection called "Stripe API" becomes `stripe-api/`. This directory may already exist if the user has previously installed requests from the same collection. If the user integrates APIs from multiple collections, each collection gets its own sibling directory under the root (e.g. `services/stripe-api/`, `services/sendgrid-api/`).

**Aim to preserve the collection's folder structure as directories.** Folders in the Postman collection become subdirectories inside the collection directory, and each request becomes a file. Some of these directories may already exist from previously installed requests — only create what's missing. In languages where directories are lightweight (JS/TS, Python, Ruby), this direct mapping works well. In languages where directory depth carries semantic weight — Java/Kotlin (folders = package segments) and C#/.NET (folders = namespace segments) — prefer flatter structures, e.g. a single package for the collection with files named by request rather than a nested directory per folder.

**Normalize names for the filesystem.** Convert Postman object names to safe directory and file names. In most languages, lowercase and replace non-alphanumeric runs with `-` (e.g. "Stripe API" becomes `stripe-api`). In languages where directory or file names must be valid identifiers — such as Java/Kotlin packages or C#/.NET namespaces — use the language's naming convention instead (e.g. `stripeapi` or `stripe_api`). If two sibling items resolve to the same name, append `-1`, `-2`, etc. (or `_1`, `_2` where hyphens aren't valid).

### Required File Header

Every installed request file MUST start with a header comment (in the language's comment syntax). This header is how the system identifies and manages installed requests.

Required fields:

- The phrase "Generated by Postman Code" (used for file discovery)
- Collection name and Collection UID
- Request path (folder hierarchy > request name) and Request UID
- Request modified-at timestamp (for update detection)

Template:

```
Generated by Postman Code

Collection: <collection name>
Collection UID: <collection uid>

Request: <request path>
Request UID: <request uid>
Request modified at: <updatedAt timestamp>
```

### Variables File

If the collection has collection-level variables or the workspace has environments, generate a variables file at the root of the collection directory.

The purpose of this file is to centralize variable values so the caller can select an environment and pass resolved values to client functions. Structure it as a mapping with:

- A `collection` key for collection-level variables
- A key for each environment, using the exact environment name from Postman (do not normalize names)

Use the language's idiomatic construct for a string-keyed mapping — an exported object in JS/TS, a dictionary in Python, a `Map<String, ...>` or similar in Java/C#, a map in Go, etc. Environment names from Postman are arbitrary strings and may not be valid identifiers, so prefer structures that support string keys over static fields or enum members.

Example (TypeScript):

```typescript
export const variables = {
  collection: {
    apiVersion: "v2",
  },
  Production: {
    baseUrl: "https://api.example.com",
    apiKey: "",
  },
  Staging: {
    baseUrl: "https://api-staging.example.com",
    apiKey: "",
  },
};
```

The caller of the generated client is responsible for selecting an environment, merging collection and environment variables, binding secrets, and passing the result to client functions. Don't do that work here.

### Function Structure

Generate a single exported function per API endpoint:

- Accept all dynamic values as explicit parameters (base URL, path variables, query params, body data, auth credentials)
- Do not hardcode variable values — the caller passes them in
- Replace Postman `{{variable}}` placeholders with function parameters
- Accept base URL and URL-related variables as function parameters
- Encode path parameters and query parameters properly
- Build the complete URL from base URL + path

### Authentication

Implement the auth scheme from the context document (request-level, folder-level, or collection-level inheritance):

- Accept credentials as function parameters — never hardcode them
- Support the auth type as documented (API key, Bearer token, Basic auth, etc.)

### Response Handling

- Parse the response payload
- If the context includes response examples, add explicit error handling for each documented status code (e.g., if the request has a 404 example, include specific 404 handling)
- Generate typed definitions for request bodies, parameters, and response shapes. Prefer the language's strongest available typing mechanism (e.g., TypeScript interfaces, JSDoc `@typedef` in JavaScript, Python TypedDicts or dataclasses, Go structs, Ruby Structs, PHP typed classes). Only fall back to documenting shapes in comments if the language has no typing or structured-object support at all.
- Follow project conventions for error handling patterns (logging, exception classes, error codes)
- Return or throw errors with meaningful context

### Documentation

- Add standard docstrings in the language's convention (JSDoc/TSDoc, Python docstrings, etc.)
- Include the request description from the context document if present
- Document all parameters, return types, and possible errors

### Extracting Shared Code

After generating multiple client files for a collection, consolidate duplicated types, auth helpers, and utility functions so they are defined once.

- Identify duplicated code across clients in the same collection
- Extract shared code and colocate it with the collection's client files using whatever mechanism is idiomatic for the language — a `shared/` subdirectory, a sibling module, a `common` subpackage, unexported helpers in the same package, etc.
- Keep shared code scoped to a single collection by default — only share across collections if the user explicitly asks

### Quality Verification

Ensure generated code is lintable, production-ready, type-safe in typed languages, and follows security best practices (no hardcoded secrets, proper input validation).

---

## API Maintenance Rules

Installed requests include metadata linking them back to their source Postman collection and request. Use these rules to help users keep their integrations current.

### Listing Installed Requests

When the user wants to see what's installed, search the project for files containing "Generated by Postman Code" in a comment within the first 15 lines. Parse each file's header to extract:

- Collection name and Collection UID
- Request path and Request UID
- Request modified-at timestamp

Present a table showing local file path (relative to project root), collection name, request path, and last modified timestamp.

### Checking for Updates

When the user wants to check for API changes, scan for installed requests as above, then for each one use `getRequestContext` to fetch the current request details. Compare the updated-at timestamp from the response to the `Request modified at` timestamp in the file header. Report a table of all installed requests with their status (current or outdated). For any outdated requests, ask the user if they want to regenerate. For confirmed updates, use `getRequestCodeContext` to re-fetch context and regenerate the file in place, matching the existing code style and updating the header timestamp.

### Finding Unused Requests

When the user wants to clean up, scan for installed requests, then for each one search the rest of the project for imports, requires, or other references to that file (by module path, relative path, or exported function name). Report any requests with zero references. Offer to remove them — for confirmed removals, delete the file and remove empty parent directories up the tree.

### Removing Installed Requests

When the user wants to remove a specific request, identify the file by path, request name, or request UID. If ambiguous, list installed requests first and ask which one. Then:

1. Delete the request file.
2. Remove empty parent directories up the tree until reaching one with contents.
3. Search the project for imports or requires referencing the deleted file. Warn the user about any broken references so they can update their code.

---

## Error Handling

**MCP not configured:**
"Run `/postman:setup` to configure the Postman MCP Server."

**401 Unauthorized:**
"Your Postman API key was rejected. Generate a new one at https://postman.postman.co/settings/me/api-keys and run `/postman:setup`."

**404 or empty response:**
"Could not find the requested resource. Check that the collection/request ID is correct."

---

## Important Notes

- Context tools return markdown — parse and use the content, don't just dump it
- Always prefer real API definitions from Postman Context over guessing from training data
- Do not expose sensitive data like tokens in output
