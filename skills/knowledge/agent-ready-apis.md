# Agent-Ready APIs: Making Your API Work for AI

## What is an Agent-Ready API?

An **agent-ready API** is one that AI agents (like Claude Code, Cursor, or autonomous coding assistants) can:

1. **Discover** - Find and understand what the API does
2. **Understand** - Know how to construct valid requests
3. **Self-heal** - Recover from errors without human intervention

When AI agents work with APIs, they don't have humans to interpret vague error messages or figure out undocumented behavior. The API itself must provide enough information for the agent to operate autonomously.

## The 8 Pillars of Agent-Readiness

Clara analyzes APIs across 8 pillars:

### 1. Machine-Consumable Metadata
**Why it matters:** Agents need unique identifiers and descriptions to reference and understand operations.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| operationId present | Critical | Unique ID to reference each operation |
| operationId descriptive | High | Meaningful names like `listUsers`, not `op1` |
| summary present | High | One-line description of what it does |
| description present | Medium | Detailed context for complex operations |
| tags present | Medium | Grouping to discover related operations |

**Fix example:**
```yaml
# Bad
paths:
  /users:
    get:
      responses: ...

# Good
paths:
  /users:
    get:
      operationId: listUsers
      summary: List all users
      description: Returns paginated list of users with optional filtering
      tags: [Users]
```

### 2. Rich Error Semantics
**Why it matters:** Agents must understand what went wrong and how to fix it.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| 4xx responses documented | Critical | Know what errors to expect |
| error schema defined | Critical | Consistent, parseable error format |
| error code field | Critical | Machine-readable code like `VALIDATION_ERROR` |
| error message field | High | Human-readable explanation |
| error details field | High | Field-level validation info |
| expected vs received | High | Exactly what was wrong |

**Fix example:**
```json
// Bad error response
{"error": "Something went wrong"}

// Good error response
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "details": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "Must be a valid email address",
      "expected": "email format (user@domain.com)",
      "received": "not-an-email"
    }
  ]
}
```

### 3. Complete Introspection
**Why it matters:** Agents construct requests from schema definitions alone.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| parameter types defined | Critical | Can't guess data types |
| required parameters marked | Critical | Know what must be provided |
| enum values listed | Critical | All valid options for choice fields |
| request/response examples | High | Concrete templates to follow |
| format/pattern specified | Medium | Validation before sending |

### 4. Consistent Naming
**Why it matters:** Predictable patterns let agents infer behavior.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| HTTP method semantics | Critical | GET reads, POST creates, etc. |
| consistent casing | High | camelCase, snake_case - pick one |
| RESTful paths | High | `/users/{id}` not `/getUser` |
| no action verbs in paths | Medium | REST patterns, not RPC |

### 5. Predictable Behavior
**Why it matters:** Agents expect consistent response formats.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| response schema defined | Critical | Can parse what comes back |
| response matches schema | Critical | No surprises |
| consistent pagination | High | Same pattern across list endpoints |
| idempotency documented | High | Safe retry behavior |

### 6. Comprehensive Documentation
**Why it matters:** Agents may fetch docs for context.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| authentication documented | Critical | How to authenticate |
| rate limits documented | High | How to throttle requests |
| docs match spec | High | Consistent information |

### 7. Speed & Reliability
**Why it matters:** Agents have timeouts and retry logic.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| response time acceptable | High | Fast enough to not timeout |
| rate limit headers | Medium | Self-throttle appropriately |
| request ID header | Medium | Correlate for debugging |

### 8. Discoverability
**Why it matters:** Agents need to find the API.

| Check | Severity | What Agents Need |
|-------|----------|-----------------|
| spec publicly accessible | High | Can fetch latest spec |
| server URL in spec | High | Know where to send requests |

## Scoring

Clara scores APIs on a 0-100 scale:

- **70%+** with no critical failures = **Agent Ready**
- **Below 70%** or critical failures = **Not Agent Ready**

Severity weights:
- Critical: 4x weight
- High: 2x weight
- Medium: 1x weight
- Low: 0.5x weight

## Common Issues and Fixes

### Missing operationIds
**Problem:** Agents can't reference operations uniquely.
**Fix:** Add descriptive operationIds to every endpoint.

### Generic error responses
**Problem:** Agent gets `{"error": "Bad request"}` and has no idea what to fix.
**Fix:** Use structured errors with field-level details.

### Undocumented authentication
**Problem:** Agent doesn't know how to authenticate.
**Fix:** Add securitySchemes and security requirements.

### Missing examples
**Problem:** Agent must construct requests from schemas alone.
**Fix:** Add realistic examples for request/response bodies.

## Running Clara

```bash
# Analyze a local spec
python scripts/analyze_agent_readiness.py ./openapi.yaml

# Analyze from URL
python scripts/analyze_agent_readiness.py --url https://api.example.com/openapi.json

# Analyze a Postman collection
python scripts/analyze_agent_readiness.py --collection <collection-id>

# Get JSON output
python scripts/analyze_agent_readiness.py ./openapi.yaml --json

# Save reports
python scripts/analyze_agent_readiness.py ./openapi.yaml -o report.json -o report.md
```

## Learn More

- **Clara Repository:** https://github.com/postmanlabs/clara
- **OpenAPI Specification:** https://spec.openapis.org/oas/latest.html
- **API Design Best Practices:** https://learning.postman.com/docs/designing-and-developing-your-api/
