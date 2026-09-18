---
name: bootstrap
description: Resolves the Postman CLI, authenticates, links the workspace, and records this repo's spec path, collections directory and workspace id. Use when the user asks to "set up Postman here", "connect this repo to Postman", "link this workspace", "authenticate with Postman", "postman login", or "run postman init" — and before the api-mocking, api-testing, api-monitoring, api-flows, performance-testing, api-discovery, or ci-integration skills only when the CLI, the linked workspace or the spec path has not already been confirmed in this session. Those skills stop and point back here if it has not completed; they never re-derive these values themselves.
---

# Bootstrap Postman for This Repo

## Overview

One-time and idempotent: every other Postman skill in this plugin reads the
values this one records and re-derives none of them. Finding an existing
`postman/` tree or an OpenAPI file is a signal to inspect, not to assume this
repo is already set up.

## Rules

- Make HTTP calls with `postman request`, never `curl` or another client — it
  reuses saved auth and env vars, syncs to the workspace, and runs test
  assertions.
- Never invent a subcommand or a flag. Run `-h` first and believe it.
- Lint specs with `postman spec lint`, never `postman api …` — the API Builder
  is deprecated in v12+ and the CLI prints no warning.
- Local commands need no login; only commands reaching the Postman cloud do.
  Don't force a login the task doesn't need.
- A missing `postman` binary means install it. Route to `postman-mcp-server`
  only after an install has been attempted and actually failed.
- Never fabricate a workspace id, spec path, or collections directory. Report
  the gap and stop.
- Never echo an API key or session token into output, logs, or summaries.
- "Present" is not "current": check the version and existing links before
  setting anything up.
- Wire up an existing repo only. Never scaffold a new API or a starter spec.
- Write no host-specific paths — one `skills/` directory loads on Claude Code,
  Cursor and Kimi Code.

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

Four steps, in order. Stop at the first that fails and report which one.

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

## 2. Authenticate, if the task needs it

### 2.1 Decide whether auth is required

Local commands need no login, and `postman init` is among them — its own help
says *"No authentication, and safe in CI."* Skip to step 3 unless something in
the task reaches the Postman cloud.

### 2.2 Sign in

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

## 3. Record the bindings

### 3.1 Check for an existing record

Read `.postman/resources.yaml` for `localResources` and `workspace.id`.
Populated → go to step 4. Absent or empty → run init.

### 3.2 Run init

`postman init --json` is the agent-facing form. It writes
`.postman/resources.yaml` and scaffolds `postman/` for specs, collections and
environments. Downstream skills read that file and nothing else.

```bash
postman init --json --no-cloud               # local only, no workspace
postman init --json --visibility personal    # also create and bind a workspace
```

**The workspace step is interactive** without `--no-cloud` or `--visibility`.

**Read the payload, not stderr.** Take `bindings` and `exitCode` from the JSON.
Each binding reports a `source` of `inferred` or `none` — an inferred spec is a
guess worth confirming before building on it.

**Exit codes that are not failures:** 2 means several specs could be
authoritative, so re-run with `--spec <path>`. 5 means the local files were
written but the requested workspace was not created — it does *not* mean re-run.

## 4. Verify and report

### 4.1 Checkpoints

- `postman --version` returned a real version.
- Auth is confirmed, or established as not required for this task.
- `.postman/resources.yaml` names a spec or a collections directory.
- `workspace.id` is set, or the run was deliberately local-only — `--no-cloud`
  leaves it empty and still exits 0, which is a pass, not a gap.

"The CLI is installed" is not the bar, and a loaded skill configures nothing.

### 4.2 Summary format

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
