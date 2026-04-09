---
description: Run Postman collection tests using the CLI
---

Run Postman collection tests to verify your API endpoints.

## Step 1: Find Collections and IDs

List collection folders and look up their cloud IDs:

```bash
ls postman/collections/
cat .postman/resources.yaml
```

The `cloudResources.collections` section maps local collection paths to cloud IDs.

If no collections found, tell the user and stop.
If one collection, use it directly.
If multiple, list them and ask which to run.

## Step 2: Run the Collection

Run by **collection ID** (from `.postman/resources.yaml`):

```bash
postman collection run <collection-id>
```

Common options:
```bash
# Stop on first failure
postman collection run <collection-id> --bail

# With request timeout
postman collection run <collection-id> --timeout-request 10000

# With environment
postman collection run <collection-id> -e ./postman/environments/<env-file>.json

# Override environment variable
postman collection run <collection-id> --env-var "base_url=http://localhost:3000"
```

## Step 3: Parse and Report Results

Parse the CLI output for pass/fail counts, failed test names, error messages, and status codes.

## Step 4: Handle Failures

If tests fail:
1. Analyze error messages
2. Read relevant source code
3. Suggest fixes
4. After fixes, re-run to verify
