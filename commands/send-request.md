---
description: Send HTTP requests using Postman CLI
---

Send an HTTP request using the Postman CLI. Ask the user what URL and method they want, or detect it from context.

## Step 1: Determine Request Details

Ask the user for:
- URL to send the request to
- HTTP method (default: GET)
- Any headers, body, or auth needed

If the user wants to send a request from a collection, find collection folders in `postman/collections/` and read the `*.request.yaml` files to extract method and URL. Collections use the v3 folder format.

## Step 2: Build and Execute

```bash
postman request <METHOD> "<URL>"
```

**With headers:** add `-H "Header: value"`
**With body:** add `-d '{"key": "value"}'`
**With bearer auth:** add `--auth-bearer-token "<token>"`
**With API key:** add `--auth-apikey-key "<name>" --auth-apikey-value "<key>"`
**With basic auth:** add `--auth-basic-username "<user>" --auth-basic-password "<pass>"`
**With environment:** add `-e ./postman/environments/<file>.json`

Always show the exact command before running it.

## Step 3: Report Results

Parse the response and report status code, response time, and body. Suggest fixes for errors (auth issues, connection problems, invalid URLs).
