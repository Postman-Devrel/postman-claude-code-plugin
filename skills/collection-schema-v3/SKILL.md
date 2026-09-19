---
name: collection-schema-v3
description: The reference for the git-native v3 collection file format — one YAML file per request/folder/example under postman/collections/, plus postman/environments/. Read before writing, editing, or generating any file in either directory by hand, or before debugging a `collection lint` failure. Covers the HTTP request/example/definition schema, environment schema, and the YAML/naming rules that make files parse — GraphQL, gRPC, WebSocket, Socket.IO, MQTT, MCP, and LLM request schemas are non-HTTP protocols and live in reference/other_protocols.md, read only when a collection actually uses one.
---

# Collection Schema (v3, Git-Native)

## Overview

A v3 collection is a directory tree under `postman/collections/`, one file
per entity — every request, every folder's metadata, every saved example is
its own file. There is no single collection.json to open and edit; the
directory structure itself *is* the collection.

```text
postman/collections/
  bookstore api/
    .resources/
      definition.yaml (optional)
      get all books.resources/
        examples/
          200 OK.example.yaml
          400 Bad Request.example.yaml
          500 Internal Server Error.example.yaml
    get all books.request.yaml
    get-book-by-id.request.yaml
    add new book.request.yaml
    authentication/
      .resources/
        definition.yaml (optional)
      signup.request.yaml
      login.request.yaml
```

- Every folder under `postman/collections/` is a collection; it can contain
  subfolders and requests.
- A folder or collection can have a `.resources/` directory — an optional
  metadata directory for that scope. `.resources/definition.yaml` holds the
  collection/folder's own metadata; request examples live under
  `.resources/<request-name>.resources/examples/`.
- Never place a request file inside a `.resources/` directory — those are
  metadata-only.

## Definition file (`.resources/definition.yaml`)

Optional metadata for a collection or folder:

- `$kind: "collection"` — required, even for a folder's definition.
- `name` — optional, defaults to the filesystem folder name.
- `description` — optional.
- `variables` — array of `{key, value, description?, disabled?}`. `value`
  must be a string; `disabled` a boolean.
- `auth` — a single auth object `{type, credentials: [{key, value}, ...]}`,
  or an array for multiAuth: `[{id, name, type, credentials, rules?}, ...]`.
- `scripts` — array of `{type, code, language: "text/javascript"}`. `type`
  is one of `http:beforeRequest`, `http:afterResponse`,
  `graphql:beforeQuery`, `graphql:afterResponse`, `grpc:beforeInvoke`,
  `grpc:onIncomingMessage`, `grpc:afterResponse`.
- `order` — number, used for folder ordering.

## HTTP request (`*.request.yaml`)

- `$kind: "http-request"` — required.
- `name` — optional (see naming rules below for when to include it).
- `order` — number; only used for relative comparison, so space values out
  (e.g. multiples of 1000) rather than packing them tight — a later
  insertion between two requests shouldn't force renumbering every sibling.
- `url` — string, with `{{varName}}` variable syntax.
- `method` — `GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS`.
- `headers` — array of `{key, value, description?, disabled?}`.
- `queryParams` — array of `{key, value, description?, disabled?}`.
- `pathVariables` — array of `{key, value, description?}`.
- `body` — `{type, content}`; `type` required whenever `body` is present.
  - Types: `json`, `formdata`, `urlencoded`, `text`, `xml`, `html`,
    `javascript`, `file`, `none`.
  - `json`/`text`/`xml`/`html`/`javascript`: `content` is a string.
  - `formdata`: `content` is an array of
    `{key, type: "text"|"file", value or src, contentType?, description?}`.
  - `urlencoded`: `content` is an array of `{key, value, description?}`.
- `auth` — `{type, credentials}`.
- `settings` —
  `{protocolVersion?, strictSSL?, followRedirects?, maxRedirects?, disabledSystemHeaders?}`.
- `scripts` — array of `{type: "beforeRequest"|"afterResponse", code, language: "text/javascript"}`.
- `examples` — optional, a relative path to the examples directory, e.g.
  `./.resources/<request-name>.resources/examples/`.

## HTTP example (`*.example.yaml`)

- `$kind: "http-example"` — required.
- `name` — optional.
- `request: {url, method}`.
- `response: {statusCode, statusText, headers: [{key, value}], body: {type, content}}`.
- `order` — optional.

Saved examples are what `collection ai-readiness` checks for — a request
with no examples scores worse for agent consumption even if perfectly
valid structurally.

## Environments (`postman/environments/*.yaml`)

- `name` — required.
- `values` — array of `{key, value: string, enabled, type}`. `value` must
  be a string (same rule as collection variables); `enabled` is boolean;
  `type` is a string, e.g. `"default"`.

## YAML rules

Invalid YAML breaks parsing silently in confusing ways — when in doubt,
single-quote it:

1. Single-quote any value containing `{{variables}}`:
   `url: '{{base_url}}/users'` — never leave it unquoted.
2. Single-quote values containing `: # & * ! [ ] { } > |`, e.g.
   `name: 'Health check: v2'`.
3. Multi-line content (JSON bodies, scripts, queries) uses a `|-` block
   scalar:
   ```yaml
   body:
     type: json
     content: |-
       {
         "name": "example"
       }
   ```
4. Quote strings that resemble booleans/numbers when a string is intended:
   `value: "true"`, `value: "123"`.
5. `order` must be a bare number, never quoted: `order: 1000`.
6. Single-quote file paths and use forward slashes only:
   `examples: './.resources/name.resources/examples'`.

## Naming rules

- `<request-name>` (the filename stem before `.request.yaml`) must not
  contain `/ \ : * ? " < > |` — sanitize to `-`.
- Include `name` in the file only when it differs from `<request-name>`
  (e.g. `name: 'Health/check'` inside `Health-check.request.yaml`, since the
  filename itself can't hold the `/`).
- Filenames must be unique, case-insensitively, per directory.

## Worked example: "bookstore api"

`postman/collections/bookstore api/get all books.request.yaml`
```yaml
$kind: http-request
method: GET
url: '{{base_url}}/books'
order: 1000
```

`postman/collections/bookstore api/get-book-by-id.request.yaml`
```yaml
$kind: http-request
name: 'get book by :id'
method: GET
url: '{{base_url}}/books/:id'
order: 2000
pathVariables:
  - key: id
    value: '1'
```

`postman/collections/bookstore api/add new book.request.yaml`
```yaml
$kind: http-request
method: POST
url: '{{base_url}}/books'
order: 3000
headers:
  - key: Content-Type
    value: application/json
body:
  type: json
  content: |-
    {
      "title": "Example Book",
      "author": "Jane Doe"
    }
```

`postman/collections/bookstore api/.resources/definition.yaml`
```yaml
$kind: collection
name: Bookstore API
variables:
  - key: base_url
    value: 'https://api.bookstore.com/v1'
```

## Critical Rules

1. **Every entity is its own file — there's no single collection.json to
   open.** A request, its parent folder's metadata, and its saved examples
   are three separate files, not sections of one document.
2. **Unquoted `{{variables}}` or special characters are the most common way
   a hand-written file fails to parse.** Single-quote per the YAML rules
   above rather than debugging a cryptic lint error after the fact.
3. **`order` is relative, not an index.** Don't renumber every sibling file
   to insert one request — leave headroom (spacing of 1000) from the start.
4. **This file covers HTTP only.** A collection using GraphQL, gRPC,
   WebSocket, Socket.IO, MQTT, MCP, or LLM requests needs
   [reference/other_protocols.md](reference/other_protocols.md) — don't
   guess those schemas from the HTTP shape above, they diverge in real ways
   (e.g. gRPC's `methodDescriptor`, LLM's `userPrompts`/`systemPrompts`).

## Reference

- [Other request protocols](reference/other_protocols.md) — GraphQL, gRPC,
  WebSocket, Socket.IO, MQTT, MCP, and LLM request schemas.
