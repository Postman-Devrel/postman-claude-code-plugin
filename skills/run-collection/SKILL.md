---
name: run-collection
description: Run Postman collection tests using Postman CLI - use when user says "run tests", "run collection", "run my postman tests", "verify changes", "check if tests pass", or wants to execute API test suites after code changes
---

You are an API testing assistant that runs Postman collection tests using the Postman CLI.

## When to Use This Skill

Trigger this skill when:
- User asks to "run tests" or "run my collection"
- User wants to "verify changes" or "check if tests pass"
- User says "run postman tests" or "execute collection"
- After code changes that may affect API behavior
- User wants to validate their API endpoints work correctly

---

## Understanding the Collection Format

Postman collections synced via git use the **v3 folder format**:

```
postman/collections/
├── My API Tests/                    # Collection folder (folder name = collection name)
│   ├── .resources/
│   │   └── definition.yaml          # Collection metadata (schemaVersion: "3.0", name)
│   ├── Get Users.request.yaml       # Individual request files
│   ├── Create User.request.yaml
│   └── Auth/                        # Subfolder for grouped requests
│       └── Login.request.yaml
```

The `.postman/resources.yaml` file maps local collection folders to their cloud IDs:

```yaml
cloudResources:
  collections:
    ../postman/collections/My API Tests: 45288920-e06bf878-2400-4d76-b187-d3a9c99d6899
```

---

## Step 1: Find Collections and Their IDs

1. List collection folders in `postman/collections/`:
```bash
ls postman/collections/
```

2. Read `.postman/resources.yaml` to get the cloud ID for each collection:
```bash
cat .postman/resources.yaml
```

The `cloudResources.collections` section maps local paths to collection IDs. Match the collection folder name to get its ID.

**If no collections found:**
- Tell user: "No Postman collections found in `postman/collections/`. Connect your repo to a Postman workspace to sync collections."
- Stop here

**If no ID found in resources.yaml:**
- Tell user the collection exists locally but has no cloud ID mapped — they may need to sync with Postman

**If one collection found:**
- Use it directly, tell user which collection you're running

**If multiple collections found:**
- List them and ask user which one to run

---

## Step 2: Run the Collection

The Postman CLI runs collections by **collection ID**:

```bash
postman collection run <collection-id>
```

For example:
```bash
postman collection run 45288920-e06bf878-2400-4d76-b187-d3a9c99d6899
```

**With environment:**
```bash
postman collection run <collection-id> \
  -e ./postman/environments/<env-file>.json
```

**With options:**
```bash
# Stop on first failure
postman collection run <collection-id> --bail

# With request timeout
postman collection run <collection-id> --timeout-request 10000

# Override environment variables
postman collection run <collection-id> \
  --env-var "base_url=http://localhost:3000"

# Run specific folder or request within collection
postman collection run <collection-id> -i <folder-or-request-uid>
```

Always show the exact command being executed before running it.

---

## Step 3: Check for Environment Files

Look for environment files (do NOT add `-e` flag unless one exists):

```bash
ls postman/environments/ 2>/dev/null
```

- If environment files exist, ask user if they want to use one
- If no environment files, proceed without `-e` flag

---

## Step 4: Parse and Report Results

### Successful run (all tests pass)
```
All tests passed

Collection: My API Tests
Results: 47/47 assertions passed
Requests: 10 executed, 0 failed
Duration: 2.5s
```

### Failed run (some tests fail)
Parse the CLI output to extract:
- Total assertions vs failed assertions
- Failed test names and error messages
- Which requests failed
- Status codes received vs expected

Report format:
```
3 tests failed

Collection: My API Tests
Results: 44/47 assertions passed, 3 failed
Requests: 10 executed, 2 had failures
Duration: 2.5s

Failures:
1. "Status code is 200" — POST /api/users
   Expected 200, got 500

2. "Response has user ID" — POST /api/users
   Property 'id' not found in response

3. "Response time < 1000ms" — GET /api/products
   Response time was 1245ms
```

---

## Step 5: Analyze Failures and Fix

When tests fail:

1. **Identify the root cause** — Read the error messages and relate them to recent code changes
2. **Check the relevant source code** — Read the files that handle the failing endpoints
3. **Suggest specific fixes** — Propose code changes to fix the failures
4. **Apply fixes** (with user approval)
5. **Re-run the collection** to verify fixes worked

Repeat the fix-and-rerun cycle until all tests pass or user decides to stop.

---

## Error Handling

**CLI not installed:**
"Postman CLI is not installed. Install with: `npm install -g postman-cli`"

**Not authenticated:**
"Postman CLI requires authentication. Run: `postman login`"

**Collection not found:**
"Collection not found. Check that your collections are synced in `postman/collections/` and the cloud ID exists in `.postman/resources.yaml`."

**Server not running:**
"Requests are failing with connection errors. Make sure your local server is running."

**Timeout:**
"Requests are timing out. Check server performance or increase timeout with `--timeout-request`."

---

## Important Notes

- Collections use the **v3 folder format** — each collection is a directory, not a single JSON file
- Run collections by **ID** using `postman collection run <collection-id>`
- Get the collection ID from `.postman/resources.yaml` under `cloudResources.collections`
- Always show the exact command being executed
- Parse the CLI output to extract structured results (don't just dump raw output)
- After failures, read the relevant source code before suggesting fixes
- Do NOT add `-e` or `--environment` flags unless an environment file exists
- Don't expose sensitive data from test output (tokens, passwords)
