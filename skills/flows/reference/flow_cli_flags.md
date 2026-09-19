# Flows CLI Flags

Captured from `postman flows <subcommand> -h` and verified on CLI
**1.58.0**. Live `-h` output is authoritative over this file — re-run it if
the installed CLI is newer, since `flows` is an actively changing surface.

Every subcommand below also accepts `--verbose`, `--debug`, and `--json`.

**Short flags are not stable across subcommands.** `-f` is `--filter` on
`list`, `--input-file` on `trigger` and `run`, and `--flow` on `list-runs`;
`-r` is `--result` on `trigger`, `--range` on `list-runs`, and `--run-id` on
`get-run`; `-t` is `--timeout` on `deploy` but `--trigger` on `update`. Read
the table for the subcommand you are actually invoking, and prefer the long
form when composing a command from more than one table.

## `flows list`

| Flag | Notes |
| --- | --- |
| `-w, --workspace <workspaceId>` | **Required** — the CLI exits 1 with `required option '-w, --workspace <workspaceId>' not specified`. |
| `-f, --filter <pattern>` | Name prefix **or** regex, e.g. `--filter "^Test.*"`. |
| `-s, --sort <criteria>` | `name` or `updated`. Default `updated`. |
| `-p, --paginate` | Page through all flows. |

## `flows trigger <flowId>`

| Flag | Notes |
| --- | --- |
| `-i, --input <key=value>` | Repeatable. Trigger payload values. |
| `-f, --input-file <path.json>` | Repeatable. Payload from JSON files. Combines with `-i`, which overrides. |
| `-q, --query <key=value>` | Repeatable. Query parameters. |
| `--headers <key=value>` | Repeatable. Custom headers. |
| `-s, --scenario <name>` | Named scenario from the flow definition; builds payload, headers and query. **`--headers` and `--query` override it.** |
| `-n, --dry-run` | Print request URL + payload, send nothing. |
| `--show-secrets` | Unmask auth tokens in dry-run output. Masked by default. |
| `-r, --result` | Print only the response body. |

## `flows deploy <flowId>`

| Flag | Notes |
| --- | --- |
| `-p, --path <path>` | **Required** — `-h` carries no `(required)` annotation, but omitting it exits 1. A suffix appended to a generated base URL, e.g. `/my-trigger`. |
| `-t, --timeout <timeout>` | HTTP session timeout, **5000ms–60000ms**, default `"10000ms"`. Value carries units — `5000ms`, not `5000`. |
| `-a, --auth` | Boolean switch. Enables auth on the trigger. Default off. |

Note the asymmetry with `update`: here `--auth` is a bare flag; on `update` it
takes `on|off`.

## `flows update <flowId>`

| Flag | Notes |
| --- | --- |
| `-t, --trigger <on\|off>` | Enable/disable the trigger. Takes an explicit value. |
| `-a, --auth <on\|off>` | Enable/disable authentication on the trigger. Takes an explicit value. |

**At least one of the two is required**: a bare `flows update <flowId>` exits 1
with `Invalid command parameters: trigger: At least one option is required:
--trigger or --auth`.

Both are mutating and confirmation-gated. `--auth off` strips authentication
from a live trigger — never run it as a convenience.

## `flows run <path>`

Runs a flow **file** locally — documented as available on Postman **Enterprise**
plans, and requires `postman login`. Inputs work as on `trigger`; the rest is
execution and reporting. Takes the path positionally; a bad path fails with
`Error: Flow file not found: <path>` and exit 1.

| Flag | Notes |
| --- | --- |
| `-i, --input <key=value>` | Repeatable. |
| `-f, --input-file <path.json>` | Repeatable. |
| `-s, --scenario <name>` | Pre-built scenario as inputs; `-i`/`-f` override values. |
| `-e, --environment <path>` | Postman environment file, JSON or YAML. |
| `--working-dir <path>` | Working directory for the run. |
| `--workspace <workspaceId>` | **Required for flows containing connector blocks.** |
| `--output <format>` | Save execution result to file. `json` only. |
| `--reporters <format>` | Save a test results report. `html` only. |
| `-x, --suppress-exit-code` | Overrides the run's exit code. Defeats CI gating. |
| `--verbose` | Per-request detail: method, URL, assertions. |
| `--no-truncate` | Full output, no truncated long values. |
| `--no-report-events` | Don't send analytics. `--report-events` exists for compatibility; analytics are on by default. |

### BETA: dataset iteration

Runs the flow once per row of a dataset view. All three are marked `[BETA]` in
the CLI's own help — confirm against live `-h` before relying on them.

| Flag | Notes |
| --- | --- |
| `--iteration-data-dataset <pathOrId>` | Local `.dataset.yaml` path or a cloud dataset id (cloud requires login). **Requires `--iteration-data-view`.** |
| `--iteration-data-view <nameOrId>` | The view within that dataset whose rows drive the run. |
| `-m, --map-column <input=column>` | Repeatable. Binds a flow input to a dataset column. Inputs whose name already matches a column bind automatically, so only map the mismatches. |
| `--no-insecure-file-read` | Blocks reading dataset files outside the working directory. |

## `flows list-runs`

| Flag | Notes |
| --- | --- |
| `-w, --workspace <workspaceId>` | **Required**, same as on `list`. |
| `-f, --flow <flowId>` | Filter sessions to one flow. |
| `-r, --range <range>` | Time range, e.g. `30m`, `2h`, `3d`. **Default `1h`** — widen it before concluding a run is missing. |

## `flows get-run`

| Flag | Notes |
| --- | --- |
| `-r, --run-id <runId>` | **Required.** The id `trigger` or `list-runs` reported. Shapes vary across Postman's own material (`session-abc123`, `main/1a123ab1`) — pass it verbatim rather than reformatting. |
| `-l, --logs` | Detailed event log. Off by default. |
| `--filter <blockId>` | Repeatable. Matches a block ID **prefix**, not an exact id. |
