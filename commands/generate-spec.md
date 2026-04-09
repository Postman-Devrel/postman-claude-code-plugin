---
description: Generate or update an OpenAPI spec from your codebase
---

Generate or update an OpenAPI 3.0 specification by analyzing API routes in your codebase.

## Step 1: Check for Existing Spec

```bash
ls postman/specs/**/*.yaml postman/specs/**/*.yml postman/specs/**/*.json 2>/dev/null
ls openapi.yaml openapi.yml swagger.yaml swagger.yml 2>/dev/null
```

If a spec exists, read it to understand current state. You'll update it rather than replace it.

## Step 2: Discover API Endpoints

Scan the project for route definitions based on the framework:

- **Express/Node**: `app.get()`, `router.post()`, `@Get()` (NestJS)
- **Python**: `@app.route()`, `@router.get()` (FastAPI), `path()` (Django)
- **Go**: `http.HandleFunc()`, `r.GET()` (Gin/Echo)
- **Java**: `@GetMapping`, `@PostMapping`, `@RequestMapping`
- **Ruby**: `get`, `post`, `resources` in routes.rb

Read the route files and extract: methods, paths, parameters, request bodies, response schemas, auth requirements.

## Step 3: Generate or Update the Spec

Write a valid OpenAPI 3.0.3 YAML spec including:
- `info` with title, version, description
- `servers` with local dev URL
- `paths` with all discovered endpoints
- `components/schemas` with models derived from code (types, models, structs)
- `components/securitySchemes` if auth is used

**When updating**: Add new endpoints, update changed ones, remove endpoints no longer in code. Preserve existing descriptions and examples.

**When creating**: Write to `postman/specs/openapi.yaml`.

## Step 4: Validate

```bash
postman spec lint ./postman/specs/openapi.yaml
```

Fix any validation errors and re-run until clean.

## Step 5: Report

Show what was created or changed:
- Endpoints documented (count and list)
- Schemas defined
- Changes from previous spec (if updating)
- Validation result
