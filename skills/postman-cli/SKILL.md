---
name: postman-cli
description: Postman CLI reference and git sync file structure knowledge - provides context for CLI-based commands (send-request, generate-spec, run-collection)
---

Reference knowledge for the Postman CLI and git sync file structure. This skill provides context used by the CLI commands.

## Postman CLI Overview

The Postman CLI (`postman-cli`) is the official command-line tool for Postman. It runs collections, validates API specs, sends requests, and integrates with CI/CD pipelines.

### Installation and Auth

```bash
npm install -g postman-cli
postman login
```

Authentication requires a valid Postman API key. Run `postman login` and follow the prompts.

### Core Commands

| Command | Purpose |
|---------|---------|
| `postman collection run <id>` | Run collection tests by cloud ID |
| `postman request <METHOD> <URL>` | Send an HTTP request |
| `postman spec lint <file>` | Validate an OpenAPI spec |
| `postman login` | Authenticate with Postman |

---

## Git Sync File Structure

When a Postman workspace is connected to a git repo, it syncs using this structure:

```
project-root/
├── .postman/
│   └── resources.yaml              # Maps local paths → cloud IDs
├── postman/
│   ├── collections/
│   │   └── My API/                  # Collection (v3 folder format)
│   │       ├── .resources/
│   │       │   └── definition.yaml  # schemaVersion: "3.0", name
│   │       ├── Get Users.request.yaml
│   │       ├── Create User.request.yaml
│   │       └── Auth/               # Subfolder
│   │           └── Login.request.yaml
│   ├── environments/
│   │   └── dev.postman_environment.json
│   └── specs/
│       └── openapi.yaml
```

### resources.yaml

Maps local collection/environment paths to their Postman cloud IDs:

```yaml
cloudResources:
  collections:
    ../postman/collections/My API: 45288920-e06bf878-2400-4d76-b187-d3a9c99d6899
  environments:
    ../postman/environments/dev.postman_environment.json: 45288920-abc12345-...
```

### Collection v3 Folder Format

Each collection is a **directory** (not a single JSON file). It contains:
- `.resources/definition.yaml` — collection metadata
- `*.request.yaml` — individual request files
- Subdirectories for folders within the collection

Request files contain:
```yaml
$kind: http-request
url: https://api.example.com/users
method: GET
order: 1000
```

---

## Postman CLI vs Newman

The Postman CLI is the **official replacement** for Newman:

| Feature | Postman CLI | Newman |
|---------|-------------|---------|
| Maintenance | Official Postman support | Community-driven |
| Security | Digitally signed binary | Open-source |
| Governance | Enterprise API governance | Not available |
| Auth | Postman API key | No authentication |
| Spec linting | Built-in | Not available |
| HTTP requests | `postman request` command | Not available |

Always use `postman-cli`, never Newman.
