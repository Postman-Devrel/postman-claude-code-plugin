# Changelog

All notable changes to the Postman Plugin for Claude Code are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version here always matches `version` in `.claude-plugin/plugin.json`. A release
is cut by tagging the matching `vX.Y.Z` (see [Releasing](#releasing)).

## [Unreleased]

## [1.3.0] - 2026-07-20

### Added

- `/postman:learn` command — searches the Postman Learning Center via the
  `searchLearningCenter` MCP tool. Requires Full MCP mode (the tool is absent in
  `minimal` and `code` modes).

## [1.2.0] - 2026-06-09

### Added

- `postman-context` skill — API discovery, exploration, and client code generation
  from real API definitions via `postman context`.

### Changed

- Reworked the unified search tool and search strategy around
  `searchPostmanElements` (`ownership` + `privateNetwork` filters).
- Reduced plugin token footprint via progressive-disclosure references and leaner
  front matter.
- Updated CI validators for scoped tools.

## [1.1.0] - 2026-04-29

### Added

- OAuth authentication support in `/postman:setup` alongside `POSTMAN_API_KEY`.

### Changed

- Added unique headers across components.

### Removed

- Redundant tooling.

## [1.0.0]

### Added

- Initial release: 11 slash commands, 7 skills, and the `readiness-analyzer`
  sub-agent, powered by the Postman MCP Server (`mcp.postman.com`) plus the
  Postman CLI for `request`, `generate-spec`, and `run-collection`.

## Releasing

Releases are automated by `.github/workflows/release.yml`. To cut a release:

1. Bump `version` in `.claude-plugin/plugin.json`.
2. Move your `## [Unreleased]` notes into a new `## [X.Y.Z] - YYYY-MM-DD` section.
3. Merge to `main`.
4. Tag the commit and push the tag:

   ```bash
   git tag v1.3.0
   git push origin v1.3.0
   ```

The workflow verifies the tag matches `plugin.json`, extracts the matching
CHANGELOG section, and publishes a GitHub Release with those notes.

[Unreleased]: https://github.com/Postman-Devrel/postman-claude-code-plugin/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/Postman-Devrel/postman-claude-code-plugin/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Postman-Devrel/postman-claude-code-plugin/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Postman-Devrel/postman-claude-code-plugin/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/Postman-Devrel/postman-claude-code-plugin/releases/tag/v1.0.0
