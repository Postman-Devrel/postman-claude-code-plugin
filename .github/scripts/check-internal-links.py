#!/usr/bin/env python3
"""Check that internal markdown links resolve to existing files."""

import re
import sys
from pathlib import Path

# Matches [text](path) and ![alt](path) — excludes URLs
LINK_RE = re.compile(r"!?\[([^\]]*)\]\(([^)]+)\)")


def check_file_links(file_path: Path, root: Path) -> list[str]:
    errors = []
    text = file_path.read_text()
    file_dir = file_path.parent

    for match in LINK_RE.finditer(text):
        target = match.group(2)

        # Skip external URLs
        if target.startswith(("http://", "https://", "mailto:")):
            continue

        # Skip anchor-only links
        if target.startswith("#"):
            continue

        # Strip anchor fragments from file paths
        target_path = target.split("#")[0]
        if not target_path:
            continue

        # Resolve relative to the file's directory
        resolved = (file_dir / target_path).resolve()
        if not resolved.exists():
            rel = file_path.relative_to(root)
            errors.append(f"{rel}: Broken link '{target}' — file not found")

    return errors


def main():
    root = Path(__file__).resolve().parent.parent.parent
    errors = []

    for md_file in sorted(root.rglob("*.md")):
        # Skip .git and node_modules
        parts = md_file.relative_to(root).parts
        if any(p.startswith(".git") or p == "node_modules" for p in parts):
            continue
        errors.extend(check_file_links(md_file, root))

    if errors:
        print("Link check failed:")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("✓ Link check passed")


if __name__ == "__main__":
    main()
