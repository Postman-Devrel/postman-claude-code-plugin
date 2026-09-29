# Environment Schema (v3)

Read this reference before creating, editing, or debugging files under
`postman/environments/`.

## Prefer the CLI for ordinary edits

The CLI preserves the schema and avoids leaking secret values into command
output:

```bash
postman environment new "Staging EU"
postman environment var set baseUrl https://staging.example.com \
  --environment "postman/environments/Staging EU.environment.yaml"
postman environment var unset oldToken \
  --environment "postman/environments/Staging EU.environment.yaml"
postman environment lint postman/environments --fail-severity warning
```

Use `environment get --show-secrets` only when the user explicitly needs the
secret value revealed. Do not print, summarize, or commit credentials returned
by it.

## File and fields

An environment is one YAML file named `<name>.environment.yaml` under
`postman/environments/`. It has no `$kind` field.

- `name` — required string.
- `values` — required array; an empty environment uses `values: []`.
- Each value has:
  - `key` — required variable name.
  - `value` — required string. Quote booleans, numbers, empty values, and
    values containing YAML punctuation or `{{variables}}` so YAML does not
    coerce them.
  - `enabled` — boolean. The CLI writes `true` for a newly set variable.
  - `type` — optional string. Use `default` for ordinary values and `secret`
    for sensitive values.
  - `description` — optional string.

Do not add collection-only fields such as `$kind`, `scripts`, `auth`, or
`variables`. Do not put secrets into an example merely to make it executable;
leave the value empty or use the team's supported secret source.

## Linted example

```yaml
name: Staging EU
values:
  - key: baseUrl
    value: 'https://staging.example.com'
    enabled: true
    type: default
    description: API base URL
  - key: apiToken
    value: ''
    enabled: false
    type: secret
```

After any hand edit, run `postman environment lint <file-or-directory>`. Use
`postman workspace lint` when the task is to validate the entire local
workspace, not just its environments.
