# Non-HTTP request schemas (v3)

Read this only when a collection actually contains one of these request
types — for the common case, the HTTP schema in the parent
[SKILL.md](../SKILL.md) is the one that applies.

## GraphQL request

- `$kind: "graphql-request"` — required.
- `url` — string.
- `order` — optional.
- `query` — string (the GraphQL query).
- `variables` — string (a YAML string containing a JSON object).
- `headers` — array of `{key, value, description?, disabled?}`.
- `auth` — `{type, credentials}`.
- `settings` — `{disabledSystemHeaders?}`.
- `scripts` — array of `{type: "beforeQuery"|"afterResponse", code, language}`.

## gRPC request

- `$kind: "grpc-request"` — required.
- `url` — string.
- `order` — optional.
- `methodPath` — string.
- `methodDescriptor` — string.
- `message` — `{content: string (JSON)}`.
- `metadata` — array of `{key, value, description?}`.
- `auth` — `{type, credentials}`.
- `settings` —
  `{secureConnection?, strictSSL?, maxResponseMessageSize?, includeDefaultFields?, connectionTimeout?}`.
- `scripts` — array of `{type: "beforeInvoke"|"afterResponse", code, language}`.

## WebSocket request

- `$kind: "websocket-request"` — required.
- `url` — string.
- `order` — optional.
- `headers` — array of `{key, value, description?, disabled?}`.
- `queryParams` — array of `{key, value, description?, disabled?}`.
- `settings` — `{handshakeTimeout?, retryCount?, retryDelay?, maxPayload?, strictSSL?}`.

## Socket.IO request

- `$kind: "socket.io-request"` — required.
- `url` — string.
- `order` — optional.
- `headers` — array of `{key, value}`.
- `queryParams` — array of `{key, value}`.
- `events` — array of `{name, description?, subscribeOnConnect: boolean}`.
- `settings` — `{version?, path?, handshakeTimeout?, retryCount?, retryDelay?, strictSSL?}`.

## MQTT request

- `$kind: "mqtt-request"` — required.
- `url` — string.
- `order` — optional.
- `clientId` — string.
- `version` — `4 | 5`.
- `topics` — array of
  `{name, qos: 0|1|2, subscribe: boolean, description?, settings: {noLocal?, retainAsPublished?, retainHandling?, subscriptionIdentifier?}}`.
- `lastWill` — `{topic, payload, qos, retain, type: "text"|"json", properties: {messageExpiryInterval?, contentType?}}`.
- `properties` —
  `{sessionExpiryInterval?, receiveMaximum?, maximumPacketSize?, requestResponseInformation?, userProperties: [{key, value}]}`.
- `settings` — `{cleanSession?, keepAlive?, autoReconnect?, connectionTimeout?, strictSSL?}`.

## MCP request

- `$kind: "mcp-request"` — required.
- `transport` — `"sse" | "stdio"`.
- `order` — optional.
- SSE shape: `{url, headers?, message, auth?, settings: {strictSSL?, requestTimeout?, sessionTimeout?}}`.
- STDIO shape: `{command, env: [{key, value}], message, auth?, settings: {requestTimeout?}}`.

## LLM request

- `$kind: "llm-request"` — required.
- `url` — string.
- `order` — optional.
- `config` — `{model, provider}`.
- `userPrompts` — array of `{id, value, timestamp, active, type: "text"}`.
- `systemPrompts` — array of `{id, value, timestamp, active, type: "text"}`.
- `mcpConfig` — optional string (JSON config).
- `enabledTools` — optional array of strings.
- `auth` — `{type, credentials}`.
- `settings` —
  `{temperature?, maxToken?, streamResponse?, responseFormatJSON?, topP?, presencePenalty?, frequencyPenalty?, maxSteps?, streamTools?}`.
