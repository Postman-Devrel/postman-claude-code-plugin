# OpenAPI 3.0 Spec Structure Template

Use this structure when generating a spec. Fill every placeholder from real code — never fabricate endpoints or schemas.

```yaml
openapi: 3.0.3
info:
  title: <API name from package.json, pyproject.toml, or project name>
  version: <version from package.json or "1.0.0">
  description: <brief description of the API>
servers:
  - url: http://localhost:<port>
    description: Local development server
paths:
  /endpoint:
    get:
      summary: <short description>
      description: <detailed description>
      operationId: <unique camelCase identifier>
      tags:
        - <group name>
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
          description: <parameter description>
      responses:
        "200":
          description: Successful response
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ModelName"
        "400":
          description: Bad request
        "401":
          description: Unauthorized
        "404":
          description: Not found
        "500":
          description: Internal server error
    post:
      summary: <short description>
      operationId: <unique camelCase identifier>
      tags:
        - <group name>
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/CreateModel"
      responses:
        "201":
          description: Created successfully
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/ModelName"
components:
  schemas:
    ModelName:
      type: object
      required:
        - id
        - name
      properties:
        id:
          type: string
          description: Unique identifier
        name:
          type: string
          description: Display name
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    apiKey:
      type: apiKey
      in: header
      name: X-API-Key
```

## Example Workflows

### Generate spec from scratch

User: "generate an openapi spec for my API"

1. Scan project for route definitions
2. Read route files and extract endpoints
3. Read models/types for schemas
4. Generate openapi.yaml
5. Validate with postman spec lint
6. Report: "Created spec with 12 endpoints and 5 schemas"

### Update spec after code changes

User: "update the spec, I added new endpoints"

1. Read existing spec
2. Scan code for all current endpoints
3. Diff against existing spec
4. Add new endpoints, update changed ones
5. Validate
6. Report: "Added 2 new endpoints, updated 1"

### Generate spec for specific routes

User: "create a spec for the user routes"

1. Find user-related route files
2. Extract only user endpoints
3. Generate focused spec
4. Validate and report
