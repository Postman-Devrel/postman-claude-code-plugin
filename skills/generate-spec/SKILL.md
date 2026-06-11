---
name: generate-spec
description: Generate or update an OpenAPI 3.0 spec from code. Use when the user wants to create, update, or write an OpenAPI/Swagger spec, API definition, or API documentation from their codebase.
---

You are an API specification assistant that generates and updates OpenAPI 3.0 specifications by analyzing the user's codebase.

## When to Use This Skill

Use this skill when the user wants to generate, create, or update an OpenAPI/Swagger spec or API definition from their existing routes and endpoints.

A reference file in this skill's directory, `references/spec-template.md`, contains the full OpenAPI structure template and example workflows. Read it with the Read tool when you reach Step 3.

---

## Step 1: Discover API Endpoints in the Codebase

Scan the project for API route definitions. Check common patterns by framework:

**Express.js / Node.js:**
```bash
# Find route files
find . -type f \( -name "*.js" -o -name "*.ts" \) -not -path "*/node_modules/*" | head -30
```
Look for: `app.get()`, `app.post()`, `router.get()`, `router.post()`, `@Get()`, `@Post()` (NestJS)

**Python (Flask/Django/FastAPI):**
```bash
find . -type f -name "*.py" -not -path "*/.venv/*" -not -path "*/venv/*" | head -30
```
Look for: `@app.route()`, `@router.get()`, `path()`, `url()`, `@app.get()` (FastAPI)

**Go:**
```bash
find . -type f -name "*.go" -not -path "*/vendor/*" | head -30
```
Look for: `http.HandleFunc()`, `r.GET()`, `e.GET()` (Echo), `router.Handle()`

**Java (Spring):**
```bash
find . -type f -name "*.java" | head -30
```
Look for: `@GetMapping`, `@PostMapping`, `@RequestMapping`, `@RestController`

**Ruby (Rails):**
```bash
find . -type f -name "routes.rb" -o -name "*controller*.rb" | head -20
```
Look for: `get`, `post`, `resources`, `namespace`

Read the relevant source files to extract:
- HTTP methods (GET, POST, PUT, PATCH, DELETE)
- URL paths and path parameters
- Query parameters
- Request body schemas (from validation, types, or models)
- Response schemas (from return types, serializers, or examples)
- Authentication requirements
- Status codes

---

## Step 2: Check for Existing Spec

Look for an existing OpenAPI spec to update:

```bash
# Check Postman specs directory
ls postman/specs/**/*.yaml postman/specs/**/*.yml postman/specs/**/*.json 2>/dev/null

# Check common root locations
ls openapi.yaml openapi.yml openapi.json swagger.yaml swagger.yml swagger.json api-spec.yaml 2>/dev/null
```

**If an existing spec is found:**
- Read it to understand current state
- Identify what's changed (new endpoints, modified schemas, removed routes)
- Update it preserving existing descriptions, examples, and custom fields
- Tell user what was added/changed/removed

**If no spec exists:**
- Create a new one at `postman/specs/openapi.yaml` (Postman's standard location)
- Create the `postman/specs/` directory if needed

---

## Step 3: Generate the OpenAPI 3.0 Spec

Read `references/spec-template.md` for the full YAML structure template, then build a valid OpenAPI 3.0 specification in YAML format following these rules:

1. **Derive from code, don't guess** — Only include endpoints that actually exist in the codebase
2. **Extract real schemas** — Use model definitions, TypeScript types, Pydantic models, or struct definitions to build component schemas
3. **Include all status codes** — Add response codes the endpoint actually returns (from error handling in code)
4. **Use $ref for shared schemas** — Define models once in `components/schemas` and reference them
5. **Group with tags** — Use tags based on route file grouping or resource names
6. **operationId** — Generate unique camelCase IDs like `getUsers`, `createUser`, `deleteUserById`
7. **Detect auth** — If middleware checks auth, add security requirements to those endpoints
8. **Port detection** — Find the server port from config files, env files, or code constants

---

## Step 4: Write the Spec File

Write the spec to the appropriate location:

- **If updating**: Write to the existing spec file path
- **If creating new**: Write to `postman/specs/openapi.yaml`
  - Create `postman/specs/` directory if it doesn't exist

Tell the user exactly where the file was written.

---

## Step 5: Validate the Spec with Postman CLI

**Always validate using the Postman CLI.** This checks for syntax errors, governance rules, and security issues configured for the team's workspace.

**Basic lint:**
```bash
postman spec lint ./postman/specs/openapi.yaml
```

**Fail on warnings too (stricter):**
```bash
postman spec lint ./postman/specs/openapi.yaml --fail-severity WARNING
```

**Output as JSON for detailed parsing:**
```bash
postman spec lint ./postman/specs/openapi.yaml --output JSON
```

**Apply workspace governance rules:**
```bash
postman spec lint ./postman/specs/openapi.yaml --workspace-id <workspace-id>
```

If the workspace ID is available in `.postman/resources.yaml`, use it to apply the team's governance rules.

**Fix-and-relint loop:**
1. Run `postman spec lint`
2. Parse the error/warning output (line numbers, severity, descriptions)
3. Fix every issue in the spec
4. Re-run `postman spec lint` until clean — no errors AND no warnings
5. Do not consider the spec complete until it passes linting

If Postman CLI is not installed, tell the user: "Install Postman CLI (`npm install -g postman-cli`) and run `postman spec lint` to validate against governance and security rules."

---

## Step 6: Report Results

Report concisely what was created or changed: the file path, endpoints documented (count and list), schemas defined, changes from the previous spec (added/updated/removed) when updating, and the validation result.

---

## Error Handling

**No API routes found:**
"Could not find API route definitions in the codebase. What framework are you using? Point me to the files containing your route definitions."

**Unsupported framework:**
"I couldn't auto-detect the framework. Please tell me which files contain your API routes and I'll generate the spec from those."

**Validation failures:**
Parse errors from `postman spec lint`, fix them in the spec, and re-validate.

**CLI not installed (for validation):**
"Spec created successfully. Install Postman CLI (`npm install -g postman-cli`) and run `postman spec lint ./postman/specs/openapi.yaml` to validate."

---

## Important Notes

- Always generate OpenAPI 3.0.3 format (widely supported, compatible with Postman)
- Use YAML format (more readable than JSON for specs)
- Derive everything from actual code — never fabricate endpoints or schemas
- Preserve existing descriptions and examples when updating a spec
- Use `$ref` references to components/schemas for reusable models
- Include realistic examples in schemas when the code provides default values or test data
- **Always run `postman spec lint`** after creating or updating a spec — do not skip this step
- The spec must pass linting with zero errors and zero warnings before it is considered done
- Use `--workspace-id` with `postman spec lint` when available to enforce team governance rules
- Place new specs in `postman/specs/openapi.yaml` to align with Postman's git sync structure
