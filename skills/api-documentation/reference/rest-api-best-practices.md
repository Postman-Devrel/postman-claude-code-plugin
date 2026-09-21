# REST API Design Practices 

- **Resource naming.** Nouns, not verbs, in the path (`POST /orders`, not
  `POST /createOrder`). Plural collections, consistent casing, nesting
  reflects real relationships and rarely goes past two levels deep.
- **HTTP methods.** GET is read-only and safe to repeat. POST creates.
  PUT replaces a whole resource and is idempotent. PATCH updates part of
  one. DELETE removes and is idempotent. Never use GET to change state.
- **Status codes.** 2xx for success (201 + `Location` on create, 204 for
  no body), 4xx for client mistakes (401 vs. 403 vs. 404 vs. 409 vs. 422
  each mean something distinct), 5xx for server failure. Inconsistent
  codes are one of the most common sources of client bugs.
- **Error responses.** One consistent shape across every endpoint, with a
  stable machine-readable `code` plus a human-readable `message`, and all
  validation failures returned together rather than one at a time.
- **Versioning.** Decide the strategy (URI path like `/v2/users`, or a
  version header) before the first breaking change forces the question.
  A breaking change is a removed/renamed field, a changed type, or a
  changed auth requirement — additive changes don't need a new version.
- **Pagination.** Page/offset pagination is simple but can skip or repeat
  items when the underlying data changes mid-list; cursor-based
  pagination avoids that and holds up better for feeds and high-write
  data. Either way, return the metadata a client needs to fetch the next
  page without guessing.
- **Filtering, sorting, searching.** Query parameters with names that say
  what they filter/sort on, not internal field names.
- **Auth.** API keys for server-to-server; OAuth bearer tokens when a
  request needs to represent a specific user, scoped rather than
  all-or-nothing. HTTPS always. Rate limits communicated through response
  headers, not discovered by hitting them.
- **Idempotency.** GET/PUT/DELETE are naturally or by-design idempotent;
  POST isn't, so a client that might retry a POST (payments, especially)
  needs an idempotency key the server can recognize on retry.
- **Content type and shape.** JSON by default; keep response bodies flat
  rather than deeply nested, and let a client ask for only the fields it
  needs on large resources.
- **Observability.** Log method, endpoint, status, and latency per
  request; return a request ID in the response so a client's bug report
  can be traced to server-side logs.
- **Backward compatibility.** Add fields instead of changing or removing
  them where possible. When something really must go, announce it, give
  a migration path, and run the old and new versions side by side for a
  window — a deprecation header on responses beats a changelog entry
  nobody reads.
- **Testing.** Beyond the happy path: auth failures, validation errors,
  rate limiting, and retries — the same edge cases a thin API-readiness
  score (see `ai-readiness`) tends to catch missing coverage for.
