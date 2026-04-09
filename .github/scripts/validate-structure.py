#!/usr/bin/env python3
"""Validate plugin structure integrity — cross-reference components."""

import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)


def has_frontmatter(path: Path) -> bool:
    text = path.read_text()
    return FRONTMATTER_RE.match(text) is not None


def main():
    root = Path(__file__).resolve().parent.parent.parent
    errors = []

    # 1. plugin.json must exist and be valid
    plugin_json = root / ".claude-plugin" / "plugin.json"
    if not plugin_json.exists():
        errors.append(".claude-plugin/plugin.json: File not found")
    else:
        try:
            json.loads(plugin_json.read_text())
        except json.JSONDecodeError:
            errors.append(".claude-plugin/plugin.json: Invalid JSON")

    # 2. .mcp.json must exist
    mcp_json = root / ".mcp.json"
    if not mcp_json.exists():
        errors.append(".mcp.json: File not found")

    # 3. Every commands/*.md must have frontmatter
    commands_dir = root / "commands"
    if commands_dir.is_dir():
        command_files = sorted(commands_dir.glob("*.md"))
        if not command_files:
            errors.append("commands/: No command files found")
        for f in command_files:
            if not has_frontmatter(f):
                errors.append(f"commands/{f.name}: Missing YAML frontmatter")
    else:
        errors.append("commands/: Directory not found")

    # 4. Every skills/*/ directory must have a SKILL.md
    skills_dir = root / "skills"
    if skills_dir.is_dir():
        skill_dirs = sorted([d for d in skills_dir.iterdir() if d.is_dir()])
        if not skill_dirs:
            errors.append("skills/: No skill directories found")
        for d in skill_dirs:
            skill_file = d / "SKILL.md"
            if not skill_file.exists():
                errors.append(f"skills/{d.name}/: Missing SKILL.md")
            elif not has_frontmatter(skill_file):
                errors.append(f"skills/{d.name}/SKILL.md: Missing YAML frontmatter")
    else:
        errors.append("skills/: Directory not found")

    # 5. Every agents/*.md must have frontmatter
    agents_dir = root / "agents"
    if agents_dir.is_dir():
        agent_files = sorted(agents_dir.glob("*.md"))
        if not agent_files:
            errors.append("agents/: No agent files found")
        for f in agent_files:
            if not has_frontmatter(f):
                errors.append(f"agents/{f.name}: Missing YAML frontmatter")
    else:
        errors.append("agents/: Directory not found")

    # 6. Check for stray markdown files in root (not README, CLAUDE, LICENSE, or examples)
    expected_root_md = {"README.md", "CLAUDE.md", "LICENSE"}
    for f in sorted(root.glob("*.md")):
        if f.name not in expected_root_md:
            errors.append(f"{f.name}: Unexpected markdown file in repo root")

    if errors:
        print("Structure validation failed:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("✓ Structure validation passed")


if __name__ == "__main__":
    main()
