# `postman search` filter syntax

Captured from `postman search <type> -h` on the installed CLI. Re-run `-h`
to check for drift before trusting this on anything version-sensitive.

## Global options (every `search <type>`)

- `--ownership <ownership>` — `organization` (or `org`, default), `external`,
  `all`.
- `-n, --limit <limit>` — max results per page, up to 25 (default 10).
- `--cursor <cursor>` — from a previous response, to paginate.
- `-o, --output <format>` — `default` (card list with a web link per
  result) or `json` (full detailed response).
- `--filter <expression>` — inline filter string.
- `--filter-json <json>` — filter as raw JSON; takes precedence over
  `--filter` if both are given.

## `--filter` expression syntax

- `=` / `!=` for a single value: `workspaceId=ws-1`
- `IN` / `NIN` for comma-separated values: `workspaceId IN ws-1,ws-2`
- Combine multiple conditions with `AND` (case-insensitive operators).
- Quote a value containing spaces or commas: `name="value with spaces"`

## `--filter-json` shape

Only a top-level `$and` array of condition objects — no `$or`, no nested
groups:

```json
{"$and":[{"workspaceId":{"$eq":"ws-abc123"}}]}
```

Each condition maps one field to one operator object: `$eq`, `$ne`, `$in`,
`$nin`.

## Fields shared across all element types

| Field | Operators | Value |
| --- | --- | --- |
| `privateNetwork` | `$eq`, `$ne` | boolean |
| `publisherIsVerified` | `$eq`, `$ne` | boolean |
| `visibility` | `$eq`, `$ne` | `internal` \| `public` \| `partner` |
| `workspaceId` | `$eq`, `$ne`, `$in`, `$nin` | id |
| `createdBy` | `$eq`, `$ne`, `$in`, `$nin` | user id |
| `organizationId` | `$eq`, `$ne`, `$in`, `$nin` | org id |
| `teamId` | `$eq`, `$ne`, `$in`, `$nin` | team id |
| `isGitConnected` | `$eq`, `$ne` | boolean |

ID filters expect actual IDs — run a broader search with `--output json`
first to find them.

## Element-specific fields

**`requests`**
| Field | Operators | Value |
| --- | --- | --- |
| `collectionId` | `$eq`, `$ne`, `$in`, `$nin` | id |
| `requestId` | `$eq`, `$ne`, `$in`, `$nin` | id |
| `method` | `$eq`, `$ne`, `$in`, `$nin` | `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, ... |
| `type` | `$eq`, `$ne`, `$in`, `$nin` | `http-request`, `graphql-request`, `grpc-request`, `ws-raw-request`, `ws-socketio-request`, `mqtt-request`, `llm-request` |

**`specs`**
| Field | Operators | Value |
| --- | --- | --- |
| `specificationId` | `$eq`, `$ne`, `$in`, `$nin` | id |

Run `postman search <type> --help` for the exhaustive per-type list — this
file covers `requests` and `specs`; the others (`collections`,
`workspaces`, `flows`, `mocks`, `environments`, `documents`) share the
common fields above plus their own, not yet captured here.

## Examples

```bash
postman search requests "login"
postman search requests "auth" --filter "method=POST AND collectionId=collection-uid-1"
postman search requests "upload" --filter "method IN POST,PUT AND workspaceId=ws-abc123"
postman search requests "payment" --ownership external --limit 5 --filter "visibility=public"
postman search specs "billing" --ownership external
postman search specs "payments" --filter "publisherIsVerified=true AND visibility=public"
```
