---
name: ai-readiness
description: Scores a Postman collection or an OpenAPI spec for how well an AI agent can discover, understand, call, and recover from errors with it — missing examples, undocumented errors, and ambiguous parameters all cost points. Use when the user asks "is my API agent-ready," "can AI agents use my API," "how agent-friendly is my API," or wants to scan, score, or improve a collection or spec for AI/agent consumption. Covers `postman collection ai-readiness` and `postman spec ai-readiness`.
---

# AI Readiness

## Overview

An "agent-ready" API is one that an AI agent can discover, understand, call correctly, and recover from errors without human intervention. Most APIs aren't there yet.

Two ways to run this check, same rubric family, different target — pick by what exists:

- `collection ai-readiness <collectionId/path>` scores a Postman collection
  — by cloud ID, local file path, or a `postman/collections/<name>`
  local-mode directory.
- `spec ai-readiness <spec>` scores an OpenAPI specification directly — by
  cloud ID or local file path — with no collection involved at all.



## Scoring

The command computes and prints the score itself — read the fields it
gives you, don't recompute them:

- **`readiness`** (score 0-100 + bucket) is the headline number. Buckets,
  low to high: **Limited → Fair → Good → Excellent**.
- **`confidence`** (`high`/`medium`/`low`) says how many signals it
  could actually measure vs. had to mark `unknown` — a data-quality
  caveat, not part of the score.

## Interpreting Results

Report the bucket, score, and confidence the command actually printed
— don't infer a percentage band. Doc coverage is a modifier via its
adjustment, not a separate gate; call it out by name when it's `low`,
since recommendations flag that first. Also state which verb ran
(`collection` vs. `spec` `ai-readiness`), which target was scored
(local path vs. cloud ID), the output mode, and — if `--min-score` was
set — the resulting exit code, not just "it passed."

You can ask user if they would like to set this check with a min score guarantee to run on their CI.

## Reference

- `collection-schema-v3` skill — what saved examples and descriptions look
  like in the git-synced format this command reads.
- `ci-integration` skill — where `--min-score` fits as a pipeline gate
  alongside `spec lint`/`collection lint`/`workspace lint`.
