# API Readiness Analysis: Pet Store API

**Date:** 2026-02-10
**Spec:** petstore-openapi.yaml
**Score:** 67/100
**Verdict:** NOT AGENT-READY (need 70+ with no critical failures)

## Pillar Scores

| Pillar | Score | Status |
|--------|-------|--------|
| Metadata | 82% | Good |
| Errors | 41% | Critical issues |
| Introspection | 72% | Acceptable |
| Naming | 91% | Excellent |
| Predictability | 63% | Needs work |
| Documentation | 35% | Critical issues |
| Performance | 52% | Needs work |
| Discoverability | 80% | Good |

## Top 5 Priority Fixes

### 1. Missing error response schemas (ERR_001) — Critical
**Affects:** 12 of 15 endpoints
**Impact:** Agents hitting errors have no idea what the response body looks like.
**Fix:** Add 4xx/5xx response schemas with error code, message, and details fields.

### 2. No rate limit documentation (DOC_003) — High
**Affects:** All endpoints
**Impact:** Agents will hammer the API with no awareness of limits.
**Fix:** Add rate limit info to API description and X-RateLimit headers to responses.

### 3. Missing request body examples (INTRO_005) — High
**Affects:** 8 POST/PUT endpoints
**Impact:** Agents must construct request bodies from scratch with no reference.
**Fix:** Add example values for each request body schema.

### 4. No pagination pattern (PRED_003) — Medium
**Affects:** 3 list endpoints
**Impact:** Agents will try to load entire datasets in one call.
**Fix:** Add limit/offset or cursor-based pagination with Link headers.

### 5. Missing parameter descriptions (META_004) — Medium
**Affects:** 22 of 45 parameters
**Impact:** Agents can't determine what values are valid for each parameter.
**Fix:** Add description field to all parameters.

## After Fixes

Re-running analysis after applying all 5 fixes:
- **New Score:** 89/100
- **Verdict:** AGENT-READY
- **Improvement:** +22 points
