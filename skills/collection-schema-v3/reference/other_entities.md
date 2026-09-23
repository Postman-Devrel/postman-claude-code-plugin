# Field reference: every v3 entity and request kind

Read this when authoring something the main guidance only names. Every field list here
is complete for its kind — a key not listed is not recognised, and the linter will
**strip it in silence** rather than report it.

## Auth

`auth` is available on a collection, a folder, a request and an example. It has two
shapes. No auth:

```yaml
auth:
  type: noauth
```

Anything else takes `type` plus `credentials`:

```yaml
auth:
  type: bearer
  credentials:
    token: '{{TOKEN}}'
```

`type` is one of `basic`, `bearer`, `apikey`, `digest`, `oauth1`, `oauth2`, `jwt`,
`awsv4`, `hawk`, `ntlm`, `asap`, `edgegrid`, `azure`, `sasl`, `inherit`. Use `inherit`
to take the parent folder's or collection's auth explicitly; omitting `auth` entirely
does the same thing.

`credentials` keys are the same names the Postman app shows for that auth type —
`username`/`password` for `basic`, `token` for `bearer`, `key`/`value`/`in` for
`apikey`, `accessKey`/`secretKey`/`region`/`service` for `awsv4`. They are not
validated against the auth type, so a wrong key name is dropped and the request goes
out unauthenticated. `credentials` accepts a map or an array of `{key, value}`; prefer
the map.

## Request body

`body` is one shape chosen by `type` — write that branch's keys and nothing else.

```yaml
body: {type: none}
```
```yaml
body:
  type: json          # or text, xml, html, javascript
  content: |-
    {"id": 1}
```
```yaml
body:
  type: urlencoded
  content:
    grant_type: client_credentials     # map, or array of {key, value, disabled?}
```
```yaml
body:
  type: formdata
  content:
    - key: file
      type: file
      src: ./payload.bin
    - key: note
      type: text
      value: hello
      contentType: text/plain
```
```yaml
body:
  type: file
  content:
    src: ./upload.bin       # an object with src, not a bare path
```

`type: json` is the one to reach for — it does not reformat the content, so write the
JSON as a block scalar. A *response* body inside an example has a narrower type list:
see Examples below.

## Scripts

```yaml
scripts:
  - type: afterResponse
    code: |-
      pm.test('ok', () => pm.response.to.have.status(200));
```

`type` is `beforeRequest` or `afterResponse` on a request, and protocol-prefixed on a
collection or folder (`http:beforeRequest`, `http:afterResponse`,
`graphql:beforeQuery`, `grpc:beforeInvoke`, …). A script entry may also carry
`language`, `packages`, and `requests`. `language` takes exactly one value,
**`text/javascript`** — `language: javascript` is a hard error,
`Invalid input: expected "text/javascript"`. Omitting it is fine.

Writing `event:` instead of `scripts:` — the v2.1 spelling — lints clean and is
dropped, leaving the request with no scripts and a run with 0 assertions.

## Request kinds

`$kind` is required on all of these, and it is the *only* required field except on
`mcp-request`, which also requires `transport`. So for every other kind a half-written
request lints clean. Fields are listed complete; `id`, `name`, `description` and `order`
are available on all of them and omitted below.

### `http-request`

`url`, `method`, `headers`, `queryParams`, `pathVariables`, `body`, `auth`, `scripts`,
`examples`, `settings`.

`settings`: `protocolVersion` (`auto`|`http1`|`http2`), `strictSSL`,
`followRedirects`, `maxRedirects`, `disabledSystemHeaders`.

`disabledSystemHeaders` is a closed list of **lowercase** header names, not free text:
`cache-control`, `postman-token`, `content-type`, `content-length`, `accept-encoding`, `user-agent`, `connection`, `accept`, `host`. `User-Agent` is rejected —
`Invalid option: expected one of "cache-control"|…|"host"`.

### `graphql-request`

`url`, `query`, `variables` (a **string** of JSON), `headers`, `auth`, `schema`,
`scripts`, `examples`, `settings`.

There is **no `queryParams`** — put query-string parameters in the `url`.

`settings`: `disabledSystemHeaders` only (same closed list as HTTP — see above).

`schema` is one shape chosen by `source`:

```yaml
schema: {source: none}
```
```yaml
schema: {source: auto}
```
```yaml
schema:
  source: file
  location: ./schema.graphql
```
```yaml
schema:
  source: api
  apiId: <id>
  versionId: <id>          # releaseId optional
```
```yaml
schema:
  source: specification
  specificationId: <id>
```

### `grpc-request`

`url`, `methodPath` (e.g. `helloworld.Greeter/SayHello`), `methodDescriptor` (an inline
proto definition), `message` (`{content}`), `metadata` (per-call headers; map or
array), `auth`, `schema`, `scripts`, `examples`, `settings`.

`settings`: `secureConnection`, `strictSSL`, `serverNameOverride`,
`maxResponseMessageSize`, `includeDefaultFields`, `connectionTimeout`.

### `websocket-request`

`url`, `headers`, `queryParams`, `messages`, `examples`, `settings`.

`messages` and `examples` are **strings** — relative paths to directories, not arrays.
An array fails with `Invalid input: expected string, received array`.

`settings`: `handshakeTimeout`, `retryCount`, `maxPayload`, `retryDelay`, `strictSSL`.

### `socket.io-request`

`url`, `headers`, `queryParams`, `events`, `messages`, `examples`, `settings`.

```yaml
events:
  - name: chat:message
    subscribeOnConnect: true
    description: Inbound chat traffic
```

`settings`: `version` (the **strings** `'2'`, `'3'`, `'4'`), `path`,
`handshakeTimeout`, `retryCount`, `retryDelay`, `strictSSL`. Bare `version: 4` is
rejected — `Invalid option: expected one of "2"|"3"|"4" (path: /settings/version)`.

### `mqtt-request`

`url`, `clientId`, `version`, `topics`, `lastWill`, `properties`, `auth`, `messages`,
`examples`, `settings`.

`version` is a **number**, either `4` or `5`, and it sits at the top level rather than
in `settings`. Do not quote it — that is the opposite of `socket.io-request`, whose
`settings.version` is the string `'2'`, `'3'` or `'4'`.

```yaml
topics:
  - name: sensors/+/temp
    qos: 1                 # a number: 0, 1 or 2
    subscribe: true
lastWill:
  topic: status/client
  payload: offline
  type: text
  qos: 0
  retain: true
```

`properties`: `sessionExpiryInterval`, `receiveMaximum`, `maximumPacketSize`,
`requestResponseInformation`, `userProperties`.

`settings`: `cleanSession`, `keepAlive`, `autoReconnect`, `connectionTimeout`,
`strictSSL`.

### `mcp-request`

Requires `$kind` **and** `transport`, which selects the legal keys. Common to both:
`message`, `auth`.

| `transport` | Its keys | `settings` |
|---|---|---|
| `stdio` | `command`, `env` (map or array) | `version`, `requestTimeout` |
| `sse` | `url`, `headers` | `version`, `requestTimeout`, `strictSSL`, `sessionTimeout` |

There are no other transports. `message` is a JSON-RPC envelope as a **string**;
`{{variables}}` interpolate inside it.

### `llm-request`

`url`, `config`, `userPrompts`, `systemPrompts`, `mcpConfig`, `enabledTools`,
`clientTools`, `auth`, `settings`.

`config` takes `model` and `provider`, both free-form strings with no fixed list, so a
typo lints clean and fails at run time.

Prompt entries are `{id, value, timestamp, active, contentType}`. **`contentType`, not
`type`** — `type` lints clean and is stripped, losing the content type.

`mcpConfig` is a **string containing a JSON array**, not nested YAML and not
`mcp.json`'s `mcpServers` object. `clientTools`, for tools the model may call with no
MCP server behind them, is `[{id, tools: [{id}]}]`.

`settings`: `temperature`, `maxToken`, `maxSteps`, `topP`, `topK`, `seed`,
`presencePenalty`, `frequencyPenalty`, `repetitionPenalty`, `contextWindow`,
`streamResponse`, `streamTools`, `responseFormatJSON`. Raise `maxSteps` when a long tool
chain has to run to completion.

## Messages

A `messages` directory holds `*.message.yaml` files. Each kind has different required
fields — this is the most common mistake in this area.

```yaml
$kind: websocket-message      # requires content + contentType
content: '{"op":"subscribe"}'
contentType: json             # text | json | xml | html | hex | base64
```

```yaml
$kind: socket.io-message      # requires eventName + args
eventName: chat:message
acknowledgement: true
args:
  - content: '{"text":"hi"}'
    contentType: json
```

```yaml
$kind: mqtt-message           # requires content + contentType + topic
topic: sensors/1/temp
content: '21.5'
contentType: text             # text | json | hex | base64
qos: 1
retain: false
```

## Examples

Examples live in `.resources/<request-name>.resources/examples/*.example.yaml`, with
`$kind` matching the request's protocol — `http-example`, `graphql-example`,
`grpc-example`, `websocket-example`, `socket.io-example`, `mqtt-example`. An
`*-example` kind is rejected in a `*.request.yaml`, and a `*-request` kind is rejected
in a `*.example.yaml`.

`http-example` requires `$kind` and `response`, and `response` requires `body`:

```yaml
$kind: http-example
name: 200 OK
request:
  method: POST
  url: https://api.example.com/orders
  headers:
    Content-Type: application/json
  body:
    type: json
    content: '{"sku":"A1"}'
response:
  statusCode: 200
  statusText: OK
  headers:
    Content-Type: application/json
  body:
    type: json
    content: '{"id":"o_1"}'
order: 1000
```

A 204 still needs a body — `body: {type: text, content: ''}`. Response `body.type`
accepts only `text`, `json`, `xml`, `html`, `javascript` and `yaml`; there is **no
`urlencoded` on a response**, so carry a form-encoded payload as `type: text` with a
matching `Content-Type` header. Request bodies do have `urlencoded`.

## Datasets

```
postman/datasets/users/
├── users.dataset.yaml
└── .resources/
    └── rows.json
```

```yaml
type: dataset                 # not $kind
name: "Users"
id: 3f2b6c1e-9d4a-4f81-bc37-5e0a71d9c402     # uuid4
data_dir: .resources
sources:
  - from: embedded_datasource
    datasource:
      name: Records
      id: 8a1d0e77-5c62-4b19-9f03-2d6e4a8b7c15
      format: json            # json | csv | xlsx | mysql
      source_type: static     # static for files, dynamic for databases
      location:
        type: local_filesystem
        value: rows.json      # relative to data_dir
views:
  - from: embedded_view
    view:
      name: Records_default_view
      id: c94e5b20-71af-4d36-8e52-0b7c6d1934fa
      query: SELECT id, name FROM Records ORDER BY id
```

`sources` and `views` are optional — `type`, `name`, `id` and `data_dir` alone is a
valid dataset, and is what `postman dataset create <path> --name X` writes.

A database source instead sets `format: mysql`, `source_type: dynamic`,
`ingest: false`, a `dsKey` and a `slug`, with `location.type: mysql`, `location.value`
a DSN and `location.table` the table name.

A view's `query` is SQL over the source `name`, not over the file name.

There is no `dataset lint`. `postman dataset get <path>` checks the structure offline.
`postman dataset query <path> -q "<sql>"` runs SQL against the source, which also proves
the data parses and the query resolves — note the `-q` flag is required, and this one
call contacts the server.

## Mocks

```
postman/mocks/probe-mock/
├── config.yaml
└── default.js
```

```yaml
version: 1                    # not $kind
id: a41c8e05-7f23-4b96-8d0e-3c6a9b25f718
name: Probe Mock
slug: probe-mock
protocol: http
port: 4500
scenarios:
  - name: default
    path: ./default.js
    default: true             # only on the default one; elsewhere omit it
```

Scenario `id` is optional. Nothing validates the `.js`, so match the shape
`postman mock generate --name X` emits — a plain Node server reading `PORT` from the
environment, one `// @endpoint METHOD /path` marker per route:

```js
const http = require('http');
const PORT = process.env.PORT || 4500;

const server = http.createServer((req, res) => {
  const url = new URL(req.url || '', 'http://localhost');
  const pathname = url.pathname;

  // @endpoint GET /health
  if (req.method === 'GET' && pathname === '/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'ok' }));
  }

  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Endpoint not defined' }));
});

server.listen(PORT);
```

Branch on `req.headers['x-mock-response-code']` to let a caller pick an error path out
of one scenario. Run it with `postman mock run <config.yaml>`, or drive it from a
collection with `postman collection run <dir> --mock <config.yaml>`.

## Environments and globals

```yaml
name: Dev
values:
  - key: base_url
    value: https://api.example.com     # always a string
    enabled: true
    type: default                      # or secret
```

Globals are identical, conventionally `name: Globals`. `values: []` is valid.

A secret value can be marked as `type: secret`, or as `secret: true` alongside
`type: default` — both are recognised fields.

Unlike `collection lint`, `environment lint` and `globals lint` **do** report an
unrecognised key, as `warning [ENV007] Unrecognized field "values.0.<key>"`. So a clean
environment lint is stronger evidence than a clean collection lint.

The **filename suffix is enforced**: `*.environment.yaml` under
`postman/environments/` and `*.globals.yaml` under `postman/globals/`.
`postman/environments/Staging.yaml` is rejected outright — *"Not an environment file.
Expected a file ending in .environment.yaml, .environment.yml, .environment.json"*.

Validate with `postman environment lint <file>` and `postman globals lint <file>`.
Both take `-o/--output` for the report format, where `collection lint` takes
`-r/--reporter`.

## Specs

`postman/specs/<name>.yaml`, or `postman/specs/<name>/` as a directory — both are
accepted on disk. The content is plain OpenAPI or AsyncAPI with no Postman wrapper.

**`$ref` does not resolve across documents.** Splitting `index.yaml` and
`components.yaml` fails whichever spelling you use —
`'#/components/schemas/X'`, `'./components.yaml#/components/schemas/X'` and
`'components.yaml#/components/schemas/X'` all report *"does not exist"*. Keep
`components` inline in the same document as the paths that reference it.

`postman spec lint` reports governance findings next to validity ones, at **ERROR**
severity. A valid spec with no `security` block still reports *"Security field is not
defined"* with issue type `Governance`, so a non-zero error count does not mean the spec
is malformed. Read the `issue type` column and treat only `Validation` findings as
format errors.

## Documents

`postman/documents/<name>.md`, plain Markdown, no front matter and no wrapper. Nothing
validates a document; it is pushed and pulled as-is.

## SDKs

An SDK is configured in `.postman/config.json`, not under `postman/`. Generate with
`postman sdk generate`, which is also the only validation.

## The workspace manifest

`.postman/resources.yaml` maps local paths to cloud ids. **Do not hand-author it** —
`postman init` creates it and `workspace push` / `mock push` maintain the mappings. The
one routine hand-edit is deleting a stale line after an entity is deleted in the cloud,
since that leaves the mapping behind.

Collections map to a **directory**; every other entity maps to a **file**. Paths are
relative to `.postman/`, so they begin `../`. Ids come either owner-prefixed
(`12345678-<uuid>`) or as bare 24-character hex — both are accepted.

```yaml
workspace:
  id: 6d3e9a17-4c80-4f25-b1a9-7e02c58d3f64
cloudResources:
  collections:
    ../postman/collections/My API: 12345678-aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
  environments:
    ../postman/environments/Dev.environment.yaml: 12345678-6d3e9a17-4c80-4f25-b1a9-7e02c58d3f64
  globals:
    ../postman/globals/Globals.globals.yaml: 12345678-99999999-8888-7777-6666-555555555555
  datasets:
    ../postman/datasets/users/users.dataset.yaml: d7c81f43-2e95-4a08-b6d1-9f3e5c07a284
  mocks:
    ../postman/mocks/probe-mock/config.yaml: a41c8e05-7f23-4b96-8d0e-3c6a9b25f718
  specs:
    ../postman/specs/orders.yaml: cccccccc-dddd-eeee-ffff-000000000000
```

An entity that exists in the cloud but is missing from this file makes `workspace push`
plan a *create*, which fails `404 The target resource was not found` and leaves the
cloud copy stale. A mapping whose path no longer exists raises `WSP014` from
`workspace lint`.

## Validating each entity

| Entity | Command |
|---|---|
| collection | `postman collection lint <dir> -r json` |
| environment / globals | `postman environment lint <file>` / `postman globals lint <file>` |
| spec | `postman spec lint <path>` |
| dataset | `postman dataset get <path>`, then `postman dataset query <path> -q "<sql>"` |
| mock | `postman mock run <config.yaml>` |
| sdk | `postman sdk generate` |
| document | none |
| everything, plus the manifest | `postman workspace lint` |

`postman workspace lint` is the broadest check, the only one with `--fix` and
`info`/`hint` severities, and the only one that reports unrecognised fields in a
*collection* (`FMT206` in a request, `FMT208` in `definition.yaml`). `collection lint`
stays silent about those, so run `workspace lint` before you call anything done.
Environment and globals lint do report their own unknown fields (`ENV007`). `postman collection run <dir> --no-report-events` is
the only way to prove scripts survived. The run needs no login; the flag suppresses the
post-run report upload, which is the only part that reaches the cloud and the only reason
a local run would fail on authentication.
