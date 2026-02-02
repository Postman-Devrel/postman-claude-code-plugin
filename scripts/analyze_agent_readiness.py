#!/usr/bin/env python3
"""
Agent-readiness analyzer for APIs using Clara.

Analyzes OpenAPI specs to determine if APIs are ready for AI agents to:
1. Discover what the API does
2. Understand how to use it correctly
3. Self-heal from errors without human intervention

Uses Clara (AI Agent API Readiness Analyzer) under the hood.

Usage:
    python analyze_agent_readiness.py <spec>
    python analyze_agent_readiness.py --url https://api.example.com/openapi.json
    python analyze_agent_readiness.py --collection <collection-id>
    python analyze_agent_readiness.py --help
"""

import sys
import os
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

CLARA_PATH = os.path.expanduser("~/work/clara/dist/cli/index.js")
MIN_NODE_VERSION = "20.0.0"


def check_node_version():
    """Check if Node.js is installed and meets version requirements."""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return None, "Node.js not found"

        version = result.stdout.strip().lstrip('v')
        major = int(version.split('.')[0])

        if major < 20:
            return None, f"Node.js {version} found, but Clara requires >= {MIN_NODE_VERSION}"

        return version, None
    except FileNotFoundError:
        return None, "Node.js not installed"
    except Exception as e:
        return None, f"Error checking Node.js: {str(e)}"


def find_clara():
    """Find Clara CLI installation."""
    if os.path.exists(CLARA_PATH):
        return CLARA_PATH, "direct"

    # Try npx fallback
    try:
        result = subprocess.run(
            ["npx", "@postman/clara", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return "@postman/clara", "npx"
    except:
        pass

    return None, None


def run_clara(args, clara_path, clara_type):
    """Run Clara CLI with given arguments."""
    if clara_type == "direct":
        cmd = ["node", clara_path] + args
    else:
        cmd = ["npx", clara_path] + args

    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120
    )


def analyze_spec(spec_path, options, clara_path, clara_type):
    """Analyze an OpenAPI spec for agent-readiness."""
    args = ["analyze", spec_path]

    if options.get('verbose'):
        args.append("--verbose")
    if options.get('json'):
        args.append("--json")
    if options.get('quiet'):
        args.append("--quiet")

    for output_path in options.get('output', []):
        args.extend(["-o", output_path])

    if options.get('probe'):
        args.append("--probe")
        if options.get('base_url'):
            args.extend(["--base-url", options['base_url']])
        if options.get('sandbox'):
            args.append("--sandbox")
        if options.get('auth'):
            args.extend(["--auth", options['auth']])

    result = run_clara(args, clara_path, clara_type)

    if result.returncode == 2:
        raise RuntimeError(f"Clara analysis failed: {result.stderr}")

    if options.get('json'):
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"error": "Failed to parse Clara output", "raw": result.stdout}

    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
        "agent_ready": result.returncode == 0
    }


def export_collection_as_openapi(collection_id, client):
    """Export a Postman collection for analysis."""
    collection = client.get_collection(collection_id)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"collection": collection}, f)
        return f.name


def format_summary(report):
    """Format a human-readable summary from the Clara report."""
    if "error" in report:
        return f"Error: {report.get('error')}"

    if "stdout" in report:
        return report["stdout"]

    summary = report.get("summary", {})
    pillars = report.get("pillars", [])
    priority_fixes = report.get("priorityFixes", [])

    lines = []
    lines.append("=" * 60)
    lines.append("AI AGENT READINESS ANALYSIS")
    lines.append("=" * 60)
    lines.append("")

    score = summary.get("overallScore", 0)
    ready = summary.get("agentReady", False)
    status = "READY" if ready else "NOT READY"
    status_emoji = "✓" if ready else "✗"

    lines.append(f"Overall Score: {score}% ({status_emoji} {status})")
    lines.append(f"Total Endpoints: {summary.get('totalEndpoints', 0)}")
    lines.append(f"  Passed: {summary.get('passed', 0)}")
    lines.append(f"  Warnings: {summary.get('warnings', 0)}")
    lines.append(f"  Failed: {summary.get('failed', 0)}")
    lines.append(f"  Critical: {summary.get('criticalFailures', 0)}")
    lines.append("")

    lines.append("Pillar Scores:")
    lines.append("-" * 40)
    for pillar in pillars:
        name = pillar.get("name", "Unknown")
        pillar_score = pillar.get("score", 0)
        passed = pillar.get("checksPassed", 0)
        failed = pillar.get("checksFailed", 0)
        total = passed + failed
        bar = "█" * (pillar_score // 10) + "░" * (10 - pillar_score // 10)
        lines.append(f"  {bar} {pillar_score:3d}% {name} ({passed}/{total})")
    lines.append("")

    if priority_fixes:
        lines.append("Top Priority Fixes:")
        lines.append("-" * 40)
        for fix in priority_fixes[:5]:
            rank = fix.get("rank", 0)
            check_name = fix.get("checkName", "Unknown")
            severity = fix.get("severity", "unknown").upper()
            affected = fix.get("endpointsAffected", 0)
            fix_summary = fix.get("summary", "")
            lines.append(f"  #{rank} [{severity}] {check_name}")
            lines.append(f"      {affected} endpoint(s) affected")
            lines.append(f"      {fix_summary}")
            lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze API agent-readiness using Clara',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python analyze_agent_readiness.py ./openapi.yaml
  python analyze_agent_readiness.py --url https://petstore3.swagger.io/api/v3/openapi.json
  python analyze_agent_readiness.py --collection 12345-abcd
  python analyze_agent_readiness.py ./openapi.yaml --json
  python analyze_agent_readiness.py ./openapi.yaml -o report.json -o report.md
        """
    )

    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('spec', nargs='?', help='Path to OpenAPI spec file')
    input_group.add_argument('--url', metavar='URL', help='URL to OpenAPI spec')
    input_group.add_argument('--collection', metavar='ID', help='Postman collection ID')

    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode')
    parser.add_argument('-o', '--output', action='append', default=[], metavar='FILE',
                       help='Output file (.json, .csv, .md)')

    probe_group = parser.add_argument_group('Live Probing Options')
    probe_group.add_argument('--probe', action='store_true', help='Enable live probing')
    probe_group.add_argument('--base-url', metavar='URL', help='Base URL for probing')
    probe_group.add_argument('--sandbox', action='store_true', help='Sandbox mode')
    probe_group.add_argument('--auth', metavar='HEADER', help='Authorization header')

    args = parser.parse_args()

    node_version, node_error = check_node_version()
    if node_error:
        print(f"Error: {node_error}", file=sys.stderr)
        print("\nClara requires Node.js >= 20.0.0", file=sys.stderr)
        sys.exit(1)

    clara_path, clara_type = find_clara()
    if not clara_path:
        print("Error: Clara not found", file=sys.stderr)
        print("\nExpected: ~/work/clara/dist/cli/index.js", file=sys.stderr)
        print("\nTo install:", file=sys.stderr)
        print("  cd ~/work/clara && npm install && npm run build", file=sys.stderr)
        sys.exit(1)

    spec_path = None
    temp_file = None

    if args.spec:
        spec_path = args.spec
    elif args.url:
        spec_path = args.url
    elif args.collection:
        try:
            from scripts.postman_client import PostmanClient
            client = PostmanClient()
            temp_file = export_collection_as_openapi(args.collection, client)
            spec_path = temp_file
            if not args.quiet:
                print(f"Exported collection {args.collection}...")
        except Exception as e:
            print(f"Error exporting collection: {e}", file=sys.stderr)
            sys.exit(1)

    options = {
        'json': args.json,
        'verbose': args.verbose,
        'quiet': args.quiet,
        'output': args.output,
        'probe': args.probe,
        'base_url': args.base_url,
        'sandbox': args.sandbox,
        'auth': args.auth,
    }

    if args.probe and not args.base_url:
        print("Error: --probe requires --base-url", file=sys.stderr)
        sys.exit(1)

    try:
        report = analyze_spec(spec_path, options, clara_path, clara_type)

        if args.json:
            print(json.dumps(report, indent=2))
        elif args.quiet:
            if "stdout" in report:
                print(report["stdout"])
        else:
            if "stdout" in report:
                print(report["stdout"])
            else:
                print(format_summary(report))

        if args.quiet:
            sys.exit(report.get("returncode", 1))
        elif "summary" in report:
            sys.exit(0 if report["summary"].get("agentReady", False) else 1)
        else:
            sys.exit(report.get("returncode", 0))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    finally:
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)


if __name__ == '__main__':
    main()
