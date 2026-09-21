<EXTREMELY_IMPORTANT>
You have the Postman plugin.

Before responding to any non-trivial API engineering task — designing, implementing, mocking, testing, monitoring, documenting, or deploying an API or Postman Flow — invoke the `postman:api-engineer` skill with the Skill tool and follow it. It is the default entry point and routes to the specific postman skills from there. Pure questions and trivial one-line edits don't need it.

When the intent is already specific, you may enter directly into the relevant skill instead: `postman:bootstrap` (link this repo to a Postman workspace), `postman:api-mocking`, `postman:api-testing`, `postman:api-monitoring`, `postman:flows`, `postman:ci-integration`, `postman:api-discovery`, `postman:ai-readiness`, `postman:performance-testing`, `postman:api-documentation`.

If you were dispatched as a subagent to execute a specific task, ignore this block — `postman:api-engineer` governs the orchestrating session, and it already shaped your dispatch.

User instructions (CLAUDE.md, AGENTS.md, direct requests) take precedence over this mandate.
</EXTREMELY_IMPORTANT>
