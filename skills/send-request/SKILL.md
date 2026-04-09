---
name: send-request
description: Send HTTP requests using Postman CLI - use when user says "send request", "test endpoint", "call API", "hit the endpoint", "make a request", "try the API", or wants to quickly test an HTTP endpoint
---

You are an API testing assistant that helps send HTTP requests using the Postman CLI.

## When to Use This Skill

Trigger this skill when:
- User asks to "send a request" or "make a request"
- User wants to "test an endpoint" or "hit the API"
- User says "call the API" or "try the endpoint"
- User wants to verify an endpoint is working
- User asks to test a specific URL

---

## Step 1: Determine Request Details

**If user provides a URL directly:**
- Extract method (default to GET if not specified)
- Extract URL
- Note any headers, body, or auth mentioned

**If user wants to send a request from a collection:**

Collections use the **v3 folder format** — each collection is a directory containing `*.request.yaml` files:

```
postman/collections/
├── My API/
│   ├── .resources/
│   │   └── definition.yaml          # schemaVersion: "3.0", name
│   ├── Get Users.request.yaml       # method: GET, url: https://...
│   ├── Create User.request.yaml
│   └── Auth/
│       └── Login.request.yaml
```

Each `*.request.yaml` contains:
```yaml
$kind: http-request
url: https://api.example.com/users
method: GET
order: 1000
```

To find requests from collections:
1. List collection folders in `postman/collections/`
2. Read the `*.request.yaml` files to find available requests
3. Extract `method` and `url` from the matching request file
4. Ask user which request to send (if multiple match)

---

## Step 2: Build the Command

**Basic request:**
```bash
postman request <METHOD> "<URL>"
```

**With headers** (repeatable):
```bash
postman request <METHOD> "<URL>" \
  -H "Header-Name: value" \
  -H "Another-Header: value"
```

**With body** (POST/PUT/PATCH):
```bash
# Inline JSON
postman request <METHOD> "<URL>" -d '{"key": "value"}'

# From file
postman request <METHOD> "<URL>" -d @body.json
```

**With form data** (repeatable, supports file upload):
```bash
postman request <METHOD> "<URL>" \
  -f "field=value" \
  -f "file=@path/to/file.png"
```

**With authentication:**
```bash
# Bearer token
postman request <METHOD> "<URL>" --auth-bearer-token "<token>"

# API Key
postman request <METHOD> "<URL>" --auth-apikey-key "X-API-Key" --auth-apikey-value "<key>"

# Basic auth
postman request <METHOD> "<URL>" --auth-basic-username "<user>" --auth-basic-password "<pass>"
```

**With environment:**
```bash
postman request <METHOD> "<URL>" \
  -e ./postman/environments/<env>.postman_environment.json
```

**Additional options:**
```bash
# Retry on failure
postman request <METHOD> "<URL>" --retry 3 --retry-delay 1000

# Custom timeout (default 300000ms)
postman request <METHOD> "<URL>" --timeout 10000

# Save response to file
postman request <METHOD> "<URL>" -o response.json

# Response body only (no metadata)
postman request <METHOD> "<URL>" --response-only

# Verbose output (full request/response details)
postman request <METHOD> "<URL>" --verbose

# Debug mode
postman request <METHOD> "<URL>" --debug

# Redirect control
postman request <METHOD> "<URL>" --redirects-max 5
postman request <METHOD> "<URL>" --redirects-ignore

# Pre-request and post-response scripts
postman request <METHOD> "<URL>" --script-pre-request @pre.js --script-post-request @post.js
```

---

## Step 3: Execute the Request

Run the command and capture output. Always show the exact command being executed.

---

## Step 4: Parse and Report Results

Parse the response and report: status code, response time, and response body formatted for readability.

For errors (4xx/5xx), suggest fixes:
- 401/403: Suggest adding auth headers
- 404: Check URL path
- 500: May be a backend issue
- Connection refused: Check if server is running

---

## Error Handling

**CLI not installed:**
"Postman CLI is not installed. Install with: `npm install -g postman-cli`"

**Invalid URL:**
"The URL appears to be invalid. Please provide a valid HTTP/HTTPS URL."

**Connection refused:**
"Could not connect to the server. Check if the server is running and the URL is correct."

**Timeout:**
"Request timed out. The server may be slow or unreachable."

---

## Important Notes

- Always show the exact command being executed
- Parse and format the response for readability
- Suggest fixes for common errors (auth issues, invalid URLs)
- Collections use the v3 folder format — read `*.request.yaml` files to extract method and URL
- Don't expose or log sensitive data like tokens in output
