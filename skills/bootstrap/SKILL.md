---
name: bootstrap
description: Resolves the Postman CLI, authenticates when the task needs it, and manages the filesystem/workspace binding for a repository. Use when the user asks to set up Postman, enable filesystem workflows, authenticate, initialize, import, connect, pull, push, sync, or share a workspace — and before skills that need a linked workspace, only when the CLI, linked workspace, or spec path has not already been confirmed.
---

# Bootstrap Postman for This Repo

## Overview

One-time and idempotent: every other Postman skill in this plugin reads the
values this one records and re-derives none of them. Finding an existing
`postman/` tree or an OpenAPI file is a signal to inspect, not to assume this
repo is already set up.

## Rules

- Make ad-hoc HTTP calls with `postman request`, never `curl` or another
  client. If the request already exists in a collection, preserve its saved
  auth, variables, scripts, and payload by using `postman collection run
  <collection-path> -i <request>` instead of reconstructing it on the command
  line; see `api-testing`.
- Never invent a subcommand or a flag. Run `-h` first and believe it.
- Lint specs with `postman spec lint`, never `postman api …` — the API Builder
  is deprecated in v12+ and the CLI prints no warning.
- Local commands need no login; only commands that reach the Postman
  workspace do. Don't force a login the task doesn't need.
- A missing `postman` binary means install it. Route to `postman-mcp-server`
  only after an install has been attempted and actually failed.
- Never fabricate a workspace id, spec path, or collections directory. Report
  the gap and stop.
- Never echo an API key or session token into output, logs, or summaries.
- "Present" is not "current": check the version and existing links before
  setting anything up.
- Wire up an existing repo only. Never scaffold a new API or a starter spec.
- Write no host-specific paths — the same `skills/` directory loads on every
  route.
- Do not use `init` or `workspace create` to share or import a workspace that
  already exists. Choose the direction of sync from the lifecycle table below.

## Ask the CLI: `-h`

The CLI is self-describing at different levels. Walk down only as far as the
question needs:

```bash
postman -h                      # resources: collection, spec, mock, monitor, workspace, api, flows…
postman <resource> -h           # that resource's actions
postman <resource> <action> -h  # real flags, defaults, and worked `Eg.` lines
```

Read the third level before writing any command that carries a flag — it is the
only place defaults are stated, and a wrong default fails silently. Live output
is authoritative over any summary, including this file. There is also no single
verb for "is the workspace linked and synced": run `postman workspace -h` and
pick from what it prints.

---

# Process

Three steps, in order. Stop at the first that fails and report which one.

## 1. Resolve the CLI

### 1.1 Check what is already there

**Present, and at which version?**

```bash
command -v postman && postman --version
```

**Current?** Never blocking — no network is a normal answer. But don't call a
feature missing without having made this comparison.

```bash
npm view postman-cli version
```

### 1.2 Install only if missing

**Preferred — npm, all platforms:**

```bash
npm install -g postman-cli
```

**Windows, or avoiding a global npm install:** use the platform installers in
[reference/cli_installation.md](reference/cli_installation.md). Every route puts
`postman` on `PATH`.

**Updating a copy that already exists:** use the same route that installed it.
curl-installed binaries don't take `npm install -g` cleanly.

**If every route fails:** name what blocked you — no Node, no shell, no write
access, or a hosted session that cannot install — then hand off to the
`postman-mcp-server` skill. An attempted install that actually failed is the
only thing that qualifies.

## 2. Establish the filesystem and workspace bindings

### 2.1 Authenticate only if this step needs it

Local commands need no login, and `postman init` is among them — its own help
says *"No authentication, and safe in CI."* Skip this entirely unless the
command you're about to run pulls or pushes an existing workspace, or shares
one with a team.

**With an API key — preferred, non-interactive:**

```bash
[ -n "$POSTMAN_API_KEY" ] && postman login --with-api-key "$POSTMAN_API_KEY"
```

**Browser flow, when that variable is unset:**

```bash
postman login
```

**Never echo the key or token.** Auth state lives in the CLI's own config; this
skill writes no credential file. Report that authentication succeeded, nothing
more.

### 2.2 Inspect both sides before choosing a command

Read `.postman/resources.yaml` for `localResources` and `workspace.id`, and
inspect the local `postman/` tree. When the user names an existing workspace or
asks to import, sync, or share one, use `workspace list --json` and `workspace
get <id> --elements --json` to confirm the workspace side. Never create a
second workspace merely because this repository is not connected yet.

Prefer filesystem-first work: materialize an existing workspace with
`workspace pull <id>`, or initialize local files with `postman init --no-cloud`
when no workspace exists. Then inspect, edit, diff, and validate the
version-controlled files before any push.

| Existing state and intent | Use | Why |
| --- | --- | --- |
| No workspace exists; start locally | `postman init --json --no-cloud` | Creates the git-native filesystem without requiring login. |
| No workspace exists; create and bind one | `postman workspace create --visibility <value>` or the explicit init creation path | Creation is the requested lifecycle event. |
| Workspace exists; enable filesystem work | `postman workspace pull <workspace-id>` | Connects the workspace to the repository and materializes its entities under `postman/`. |
| Workspace exists; record only the Git binding | `postman workspace connect-git <workspace-id> [path]` | Binds without downloading its contents. |
| Bound workspace; the workspace is authoritative | `postman workspace pull` | Refreshes local files from the connected workspace. |
| Bound workspace; local files are authoritative | `postman workspace diff --push-strategy default`, then `postman workspace push` | Previews and publishes creates/updates without deleting unmatched workspace entities. |
| “Share this existing workspace with my team” and it is already team-accessible | Diff, then `postman workspace push` | Publishes local contents to the existing workspace; `create` would make a duplicate. |

If “share” also requires changing a personal workspace's visibility or team
permissions, inspect its metadata first. `push` synchronizes entities; it does
not change access control. Do not create a replacement to work around a missing
metadata-update command.

`workspace diff` is read-only. Match its push strategy to the intended push.
`--push-strategy force-sync` can delete workspace entities absent locally, so use it
only when the user explicitly requests mirroring and approves the shown
deletions. Do not add `-y` merely to bypass a prompt.

### 2.3 Initialize only when there is no workspace to pull

`postman init --json` is the agent-facing form. It writes
`.postman/resources.yaml` and scaffolds `postman/` for specs, collections and
environments. Downstream skills read that file and nothing else.

```bash
postman init --json --no-cloud               # local only, no workspace
postman init --json --visibility personal    # also create and bind a workspace
```

Use `--visibility` only when a new workspace is actually wanted. If the
workspace already exists, use `pull` to enable the filesystem workflow;
use `push` only when publishing local changes to an already-bound workspace.

**The workspace step is interactive** without `--no-cloud` or `--visibility`.

**Read the payload, not stderr.** Take `bindings` and `exitCode` from the JSON.
Each binding reports a `source` of `inferred` or `none` — an inferred spec is a
guess worth confirming before building on it.

**Exit codes that are not failures:** 2 means several specs could be
authoritative, so re-run with `--spec <path>`. 5 means the local files were
written but the requested workspace was not created — it does *not* mean re-run.

## 3. Verify and report

### 3.1 Checkpoints

- `postman --version` returned a real version.
- Auth is confirmed, or established as not required for this task.
- `.postman/resources.yaml` names a spec or a collections directory.
- `workspace.id` is set, or the run was deliberately local-only — `--no-cloud`
  leaves it empty and still exits 0, which is a pass, not a gap.
- After `pull`, expected workspace entities exist under `postman/`. After
  `push`, report created/updated entities and conflicts; do not claim a
  workspace is shared unless its access level permits the intended teammates.

"The CLI is installed" is not the bar, and a loaded skill configures nothing.

### 3.2 Summary format

```md
## Postman bootstrap
- **CLI**: <version> (latest: <version> | not checked)
- **Auth**: <api-key | browser | not required for this task>
- **Workspace**: <id | none — local only>
- **Spec path**: <path (inferred | explicit) | none — user must create>
- **Collections dir**: <path | none — user must create>
```

---

# Reference Files

- `collection-schema-v3` skill — read when inspecting or writing the
  collection files this skill resolves.
- [CLI Installation](reference/cli_installation.md) — read for install, update
  and uninstall commands per platform.
