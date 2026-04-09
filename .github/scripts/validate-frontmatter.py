#!/usr/bin/env python3
"""Validate YAML frontmatter in commands, skills, and agents."""

import re
import sys
from pathlib import Path
from typing import Optional

# PyYAML is not guaranteed on all runners, so parse simple YAML manually
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)

KNOWN_TOOLS = {"Bash", "Read", "Write", "Glob", "Grep", "mcp__postman__*"}


def parse_frontmatter(text: str) -> Optional[dict]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    result = {}
    for line in match.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value
    return result


def validate_commands(root: Path) -> list[str]:
    errors = []
    commands_dir = root / "commands"
    if not commands_dir.is_dir():
        return [f"{commands_dir}: Directory not found"]

    for f in sorted(commands_dir.glob("*.md")):
        text = f.read_text()
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"{f.name}: Missing YAML frontmatter")
            continue
        if "description" not in fm or not fm["description"]:
            errors.append(f"{f.name}: Missing required field 'description'")
        if "allowed-tools" in fm and fm["allowed-tools"]:
            tools = [t.strip() for t in fm["allowed-tools"].split(",")]
            for tool in tools:
                if tool not in KNOWN_TOOLS:
                    errors.append(f"{f.name}: Unknown tool '{tool}' in allowed-tools")

    return errors


def validate_skills(root: Path) -> list[str]:
    errors = []
    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        return [f"{skills_dir}: Directory not found"]

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            errors.append(f"skills/{skill_dir.name}/: Missing SKILL.md")
            continue
        text = skill_file.read_text()
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Missing YAML frontmatter")
            continue
        if "name" not in fm or not fm["name"]:
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Missing required field 'name'")
        if "description" not in fm or not fm["description"]:
            errors.append(f"skills/{skill_dir.name}/SKILL.md: Missing required field 'description'")

    return errors


def validate_agents(root: Path) -> list[str]:
    errors = []
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return [f"{agents_dir}: Directory not found"]

    required_fields = ["name", "description", "model", "allowed-tools"]

    for f in sorted(agents_dir.glob("*.md")):
        text = f.read_text()
        fm = parse_frontmatter(text)
        if fm is None:
            errors.append(f"agents/{f.name}: Missing YAML frontmatter")
            continue
        for field in required_fields:
            if field not in fm or not fm[field]:
                errors.append(f"agents/{f.name}: Missing required field '{field}'")
        if "allowed-tools" in fm and fm["allowed-tools"]:
            tools = [t.strip() for t in fm["allowed-tools"].split(",")]
            for tool in tools:
                if tool not in KNOWN_TOOLS:
                    errors.append(f"agents/{f.name}: Unknown tool '{tool}' in allowed-tools")

    return errors


def main():
    root = Path(__file__).resolve().parent.parent.parent
    errors = []

    errors.extend(validate_commands(root))
    errors.extend(validate_skills(root))
    errors.extend(validate_agents(root))

    if errors:
        print("Frontmatter validation failed:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("✓ Frontmatter validation passed")


if __name__ == "__main__":
    main()
