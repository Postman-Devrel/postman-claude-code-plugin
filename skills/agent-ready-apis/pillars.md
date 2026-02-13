# The 8 Pillars of Agent Readiness

## Metadata (META)

| Check | Description | Severity |
|-------|-------------|----------|
| META_001 | Every operation has an `operationId` | Critical |
| META_002 | Every operation has a `summary` | High |
| META_003 | Every operation has a `description` | Medium |
| META_004 | All parameters have descriptions | Medium |
| META_005 | Operations are grouped with tags | Medium |
| META_006 | Tags have descriptions | Low |

**Why agents care:** Agents need to discover and select the right endpoint from a list. Without operationIds, agents can't reliably reference endpoints. Without summaries and descriptions, agents can't determine which endpoint matches their goal.

## Errors (ERR)

| Check | Description | Severity |
|-------|-------------|----------|
| ERR_001 | 4xx error responses defined for each endpoint | Critical |
| ERR_002 | Error schemas include machine-readable identifier and human-readable message | Critical |
| ERR_003 | 5xx error responses defined | High |
| ERR_004 | 429 Too Many Requests response defined | High |
| ERR_005 | Error examples provided | Medium |
| ERR_006 | Retry-After header documented for 429/503 | Medium |

**Why agents care:** Agents need to self-heal when things go wrong. Without structured error schemas, an agent hitting a 400 has no idea how to parse the error or recover. Without 429 documentation, agents hammer APIs until blocked.

## Introspection (INTRO)

| Check | Description | Severity |
|-------|-------------|----------|
| INTRO_001 | All parameters have `type` defined | Critical |
| INTRO_002 | Required fields are marked | Critical |
| INTRO_003 | Enum values used for constrained fields | High |
| INTRO_004 | String parameters have `format` where applicable | Medium |
| INTRO_005 | Request body examples provided | High |
| INTRO_006 | Response body examples provided | Medium |

**Why agents care:** Agents need to construct valid requests without guessing. Missing types force agents to guess formats. Missing required field markers lead to validation errors. Missing examples mean agents build request bodies from scratch with no reference.

## Naming (NAME)

| Check | Description | Severity |
|-------|-------------|----------|
| NAME_001 | Consistent casing in paths (kebab-case preferred) | High |
| NAME_002 | RESTful path patterns (nouns, not verbs) | High |
| NAME_003 | Correct HTTP method semantics | Medium |
| NAME_004 | Consistent pluralization in resource names | Medium |
| NAME_005 | Consistent property naming convention | Medium |
| NAME_006 | No abbreviations in public-facing names | Low |

**Why agents care:** Agents need predictable patterns to reason about. Inconsistent naming means agents can't predict URL patterns, leading to wrong endpoint calls. Verb-based paths break REST mental models that agents rely on.

## Predictability (PRED)

| Check | Description | Severity |
|-------|-------------|----------|
| PRED_001 | All responses have schemas defined | Critical |
| PRED_002 | Consistent response envelope pattern | High |
| PRED_003 | Pagination documented for list endpoints | High |
| PRED_004 | Consistent date/time format (ISO 8601) | Medium |
| PRED_005 | Consistent ID format across resources | Medium |
| PRED_006 | Nullable fields explicitly marked | Medium |

**Why agents care:** Agents need to parse responses reliably. Missing schemas mean agents can't validate what they receive. No pagination documentation means agents try to load entire datasets in one call. Inconsistent date formats cause parsing failures.

## Documentation (DOC)

| Check | Description | Severity |
|-------|-------------|----------|
| DOC_001 | Authentication documented in security schemes | Critical |
| DOC_002 | Auth requirements per endpoint | High |
| DOC_003 | Rate limits documented | High |
| DOC_004 | API description provides overview | Medium |
| DOC_005 | External documentation links provided | Low |
| DOC_006 | Terms of service and contact info | Low |

**Why agents care:** Agents need context that humans get from reading docs. Without auth documentation, agents can't authenticate. Without rate limit documentation, agents have no awareness of usage constraints.

## Performance (PERF)

| Check | Description | Severity |
|-------|-------------|----------|
| PERF_001 | Rate limit headers documented (X-RateLimit-*) | High |
| PERF_002 | Cache headers documented (ETag, Cache-Control) | Medium |
| PERF_003 | Compression support noted | Medium |
| PERF_004 | Bulk/batch endpoints for high-volume operations | Low |
| PERF_005 | Partial response support (fields parameter) | Low |
| PERF_006 | Webhook/async patterns for long-running operations | Low |

**Why agents care:** Agents need to operate within constraints. Without rate limit headers in responses, agents can't self-throttle. Without cache headers, agents re-fetch data unnecessarily. Without bulk endpoints, agents make hundreds of individual calls.

## Discoverability (DISC)

| Check | Description | Severity |
|-------|-------------|----------|
| DISC_001 | OpenAPI 3.0+ used | High |
| DISC_002 | Server URLs defined | Critical |
| DISC_003 | Multiple environments documented (staging, prod) | Medium |
| DISC_004 | API version in URL or header | Medium |
| DISC_005 | CORS documented | Low |
| DISC_006 | Health check endpoint exists | Low |

**Why agents care:** Agents need to find and connect to the API. Missing server URLs mean agents have no idea where to send requests. Older spec formats (Swagger 2.0) have less machine-readable information for agents to work with.

## Scoring Formula

For each check:
- If N/A (e.g., no list endpoints for pagination check): exclude from scoring
- If applicable: `weight * (passing_items / total_items)`

Pillar score: `sum(weighted_scores) / sum(applicable_weights) * 100`
Overall score: `sum(all_weighted_scores) / sum(all_applicable_weights) * 100`

Severity weights: Critical = 4, High = 2, Medium = 1, Low = 0.5
