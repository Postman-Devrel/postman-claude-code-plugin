#!/usr/bin/env python3
"""Validate JSON config files for the Claude Code plugin."""

import json
import sys
from pathlib import Path


def validate_plugin_json(path: Path) -> list[str]:
    errors = []
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"{path}: Invalid JSON — {e}"]

    required_fields = ["name", "version", "description"]
    for field in required_fields:
        if field not in data:
            errors.append(f"{path}: Missing required field '{field}'")
        elif not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"{path}: Field '{field}' must be a non-empty string")

    if "version" in data and isinstance(data["version"], str):
        parts = data["version"].split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            errors.append(f"{path}: Field 'version' must be semver (e.g. 1.0.0)")

    return errors


def validate_mcp_json(path: Path) -> list[str]:
    errors = []
    try:
        with open(path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"{path}: Invalid JSON — {e}"]

    if "mcpServers" not in data:
        errors.append(f"{path}: Missing required key 'mcpServers'")
    elif not isinstance(data["mcpServers"], dict):
        errors.append(f"{path}: 'mcpServers' must be an object")
    else:
        for name, config in data["mcpServers"].items():
            if "type" not in config:
                errors.append(f"{path}: Server '{name}' missing 'type'")
            if "url" not in config:
                errors.append(f"{path}: Server '{name}' missing 'url'")

    return errors


def main():
    root = Path(__file__).resolve().parent.parent.parent
    errors = []

    plugin_json = root / ".claude-plugin" / "plugin.json"
    if plugin_json.exists():
        errors.extend(validate_plugin_json(plugin_json))
    else:
        errors.append(f"{plugin_json}: File not found")

    mcp_json = root / ".mcp.json"
    if mcp_json.exists():
        errors.extend(validate_mcp_json(mcp_json))
    else:
        errors.append(f"{mcp_json}: File not found")

    if errors:
        print("JSON validation failed:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("✓ JSON validation passed")


if __name__ == "__main__":
    main()
