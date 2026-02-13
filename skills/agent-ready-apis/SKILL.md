---
name: agent-ready-apis
description: Knowledge about AI agent API compatibility. Use when user asks about API readiness, agent compatibility, or wants to improve their API for AI consumption.
user-invocable: false
---

# Agent-Ready APIs

An "agent-ready" API is one that an AI agent can discover, understand, call correctly, and recover from errors without human intervention. Most APIs aren't there yet.

## When to Suggest the Analyzer

If the user mentions any of these, suggest running the readiness-analyzer agent:
- "Is my API agent-ready?"
- "Can AI agents use my API?"
- "Scan my API" / "Analyze my spec"
- "What's wrong with my API for AI?"
- "How agent-friendly is my API?"
- "Improve my API for AI agents"

## What Gets Evaluated

The analyzer checks 48 items across 8 pillars:

| Pillar | What It Measures |
|--------|-----------------|
| Metadata | operationIds, summaries, descriptions, tags |
| Errors | Error schemas, codes, messages, retry guidance |
| Introspection | Parameter types, required fields, enums, examples |
| Naming | Consistent casing, RESTful paths, HTTP semantics |
| Predictability | Response schemas, pagination, date formats |
| Documentation | Auth docs, rate limits, external links |
| Performance | Rate limit headers, cache, bulk endpoints, async patterns |
| Discoverability | OpenAPI version, server URLs, contact info |

## Scoring

- **Critical checks (4x weight):** Blocks agent usage entirely
- **High checks (2x weight):** Causes frequent agent failures
- **Medium checks (1x weight):** Degrades agent performance
- **Low checks (0.5x weight):** Nice-to-have improvements

**Agent Ready = score of 70% or higher with zero critical failures.**

## Interpreting Results

- **90-100%:** Excellent. Agents can use this API reliably.
- **70-89%:** Agent-ready. Minor improvements possible.
- **50-69%:** Not agent-ready. Key issues need fixing.
- **Below 50%:** Significant work needed. Focus on critical failures first.

See `pillars.md` in this skill folder for the full check reference.
