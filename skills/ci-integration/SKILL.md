---
name: ci-integration
description: Common CI integrations that can added as independent pass/fail gates. Use when the user asks to "add Postman to CI," "run this collection on every PR," "fail the build on a governance violation," or "push to the postman cloud workspace after merge to main", "add some api related operation in my Github actions". 
---

# CI Integration

## Overview
These are some common workflows that one can add in their CI pipeline leveraging postman cli.

## Run a collection — a gated pipeline step

`postman collection run <path/id>` exits nonzero on a failed `pm.test`
assertion, which is what makes it a usable gate — see `api-testing` for how
that exit code actually gets set. What's CI-specific: `-r junit,html` (or
`--reporter-*-export`) writes a report your CI provider can surface as
build artifacts or test annotations, instead of leaving the result buried in
a log. `--bail` stops the run early on the first failure when a fast signal
matters more than a full report.

## Lint — pick the target that matches the gate you want

Three verbs look interchangeable and aren't — only two of them apply your
organization's governance rules, and the CLI's own `-h` output is where that
becomes visible (no assumption below goes further than what it printed):

| Want to check | Command | Applies org governance? |
| --- | --- | --- |
| One spec against your rules | `spec lint <spec> --workspace-id <id> -f error` | Yes, via `--workspace-id` |
| One collection's structure/style | `collection lint <path> -f error` | **No** — this verb takes no `--workspace-id` at all |
| The whole workspace: every entity plus `.postman/resources.yaml` | `workspace lint --workspace-id <id> -f error` | Yes |

`collection lint` is a schema/style check only — running it and reporting
"governance passed" overstates what it did. If the ask is "does this
collection violate our rules," `workspace lint` is the one that actually
answers it (and covers every collection in the repo in one pass); reach for
bare `collection lint` only when there's no workspace to fetch rules from
yet.

## Push to workspace — only after merge

`postman workspace push -y` is the one command in this skill that changes
shared cloud state, so it belongs behind a merge-to-main trigger, not a PR
trigger. `-y` skips confirmation prompts a non-interactive job can't answer.
Leave `--no-prepare` off — the default prepare step is what assigns real IDs
to entities that are new since the last push; skipping it because a run
felt slow trades a few seconds for a push that silently fails to create
anything new.

`--push-strategy force-sync` mirrors the whole workspace, deleting any cloud
entity with no local counterpart — genuinely destructive, and not the
default for a reason. See Critical Rules before adding it to a merge job.

## Critical Rules

1. **Never collapse `run` and `lint` into one step, and never pass
   `-x`/`--suppress-exit-code` to a CI run.** One combined exit code hides
   which check broke; a suppressed one hides that anything broke at all.
2. **Gate `workspace push` to the merge event, never a PR event.** Everything
   else in this skill is read-only against the cloud; this is the one
   command that writes to it, so a PR-triggered push ships an unmerged
   branch's entities to the shared workspace.
3. **`--push-strategy force-sync` deletes cloud entities absent locally.**
   Only add it to a job whose explicit job is mirroring the workspace exactly,
   with that intent confirmed — never as the default merge step, where the
   default (create/update-only) strategy is the safe choice.
4. **Authenticate once, non-interactively:**
   `postman login --with-api-key "$POSTMAN_API_KEY"`, reading the key from
   the CI provider's secret store. Don't reach for `collection run`'s
   `--postman-api-key` as the general answer — it's US-region only — and
   `spec lint`/`workspace push` don't take it at all.

   ```yaml
   # WRONG — key committed in plain text, and scoped to one command anyway
   - run: postman collection run api.json --postman-api-key PMAK-abc123...

   # CORRECT — one non-interactive login, key from the provider's secret store
   - run: postman login --with-api-key "$POSTMAN_API_KEY"
   - run: postman collection run api.json
   - run: postman spec lint spec.yaml --workspace-id $WS -f error
   ```
5. **Never `newman run` in place of `postman collection run`.** The CLI is
   the supported runner every other skill here assumes; Newman forks the
   toolchain and skips whatever reporting/governance depends on the CLI
   specifically.

## Verification

State each gate that ran and its individual result — not "CI passed," but
which check ran, what it checked (governance vs. structure, per the Lint
table above), and its exit code. If `workspace push` ran, confirm it was
triggered by the merge event and not a PR event, state which push strategy
was used, and report `Created`/`Updated` per entity rather than just "push
succeeded." Confirm no secret value appears literally in the committed
workflow file.

## Reference

- `api-testing` skill — `collection run`'s exit-code semantics and reporter
  flags in full.
- `spec-authoring` skill — `spec lint` and governance rulesets.
- `collection-schema-v3` skill — what `workspace push` is actually pushing.
- `bootstrap` skill — CLI resolution, workspace linking, `.postman/resources.yaml`.
