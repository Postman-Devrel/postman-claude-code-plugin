#!/usr/bin/env python3
"""
Detect breaking changes between API versions.

Analyzes two OpenAPI specifications or Postman collections and identifies
breaking changes that would affect API consumers.

Breaking changes include:
- Removed endpoints
- Removed required parameters
- Changed parameter types
- Removed response fields
- Changed authentication requirements
- HTTP method changes

Usage:
    python detect_breaking_changes.py --api <api-id> --old-version <v1> --new-version <v2>
    python detect_breaking_changes.py --spec <spec-id-1> <spec-id-2>
    python detect_breaking_changes.py --collection <col-id-1> <col-id-2>
    python detect_breaking_changes.py --file <old.json> <new.json>
    python detect_breaking_changes.py --help
"""

import sys
import os
import argparse
import json
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


class BreakingChangeDetector:
    """Detect breaking changes between API versions."""

    def __init__(self):
        self.breaking_changes = []
        self.non_breaking_changes = []

    def add_breaking(self, category, message, severity="high"):
        """Add a breaking change."""
        self.breaking_changes.append({
            "category": category,
            "message": message,
            "severity": severity
        })

    def add_non_breaking(self, category, message):
        """Add a non-breaking change."""
        self.non_breaking_changes.append({
            "category": category,
            "message": message
        })

    def compare_openapi_specs(self, old_spec, new_spec):
        """Compare two OpenAPI specifications."""
        print("🔍 Analyzing API Changes...\n")

        old_paths = old_spec.get('paths', {})
        new_paths = new_spec.get('paths', {})

        # Check for removed endpoints
        for path in old_paths:
            if path not in new_paths:
                self.add_breaking(
                    "Removed Endpoint",
                    f"Endpoint removed: {path}",
                    "critical"
                )
                continue

            old_methods = old_paths[path]
            new_methods = new_paths[path]

            # Check each method
            for method in old_methods:
                if method not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    continue

                if method not in new_methods:
                    self.add_breaking(
                        "Removed Method",
                        f"Method removed: {method.upper()} {path}",
                        "critical"
                    )
                    continue

                # Compare operations
                old_op = old_methods[method]
                new_op = new_methods[method]

                self._compare_operation(path, method, old_op, new_op)

        # Check for added endpoints (non-breaking)
        for path in new_paths:
            if path not in old_paths:
                self.add_non_breaking(
                    "Added Endpoint",
                    f"New endpoint: {path}"
                )
                continue

            new_methods = new_paths[path]
            old_methods = old_paths.get(path, {})

            for method in new_methods:
                if method not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    continue

                if method not in old_methods:
                    self.add_non_breaking(
                        "Added Method",
                        f"New method: {method.upper()} {path}"
                    )

    def _compare_operation(self, path, method, old_op, new_op):
        """Compare two operations."""
        location = f"{method.upper()} {path}"

        # Compare parameters
        old_params = old_op.get('parameters', [])
        new_params = new_op.get('parameters', [])

        old_param_map = {(p['name'], p.get('in', 'query')): p for p in old_params}
        new_param_map = {(p['name'], p.get('in', 'query')): p for p in new_params}

        # Check for removed parameters
        for key, param in old_param_map.items():
            name, location_type = key

            if key not in new_param_map:
                if param.get('required', False):
                    self.add_breaking(
                        "Removed Required Parameter",
                        f"{location}: Removed required {location_type} parameter '{name}'",
                        "critical"
                    )
                else:
                    self.add_non_breaking(
                        "Removed Optional Parameter",
                        f"{location}: Removed optional {location_type} parameter '{name}'"
                    )
            else:
                # Check if parameter changed
                new_param = new_param_map[key]

                # Check if optional became required
                if not param.get('required', False) and new_param.get('required', False):
                    self.add_breaking(
                        "Parameter Now Required",
                        f"{location}: Parameter '{name}' is now required",
                        "high"
                    )

                # Check if type changed
                old_type = param.get('schema', {}).get('type')
                new_type = new_param.get('schema', {}).get('type')

                if old_type and new_type and old_type != new_type:
                    self.add_breaking(
                        "Parameter Type Changed",
                        f"{location}: Parameter '{name}' type changed from {old_type} to {new_type}",
                        "high"
                    )

        # Check for added required parameters
        for key, param in new_param_map.items():
            name, location_type = key

            if key not in old_param_map and param.get('required', False):
                self.add_breaking(
                    "New Required Parameter",
                    f"{location}: Added required {location_type} parameter '{name}'",
                    "high"
                )

        # Compare request body
        old_body = old_op.get('requestBody', {})
        new_body = new_op.get('requestBody', {})

        # Check if request body removed
        if old_body and not new_body:
            self.add_breaking(
                "Request Body Removed",
                f"{location}: Request body removed",
                "critical"
            )

        # Check if request body became required
        if not old_body.get('required', False) and new_body.get('required', False):
            self.add_breaking(
                "Request Body Now Required",
                f"{location}: Request body is now required",
                "high"
            )

        # Compare responses
        old_responses = old_op.get('responses', {})
        new_responses = new_op.get('responses', {})

        # Check for removed success responses
        for code in old_responses:
            if code.startswith('2') and code not in new_responses:
                self.add_breaking(
                    "Response Removed",
                    f"{location}: Success response {code} removed",
                    "high"
                )

        # Compare security
        old_security = old_op.get('security', [])
        new_security = new_op.get('security', [])

        if old_security != new_security:
            if not old_security and new_security:
                self.add_breaking(
                    "Authentication Required",
                    f"{location}: Authentication now required",
                    "high"
                )
            elif old_security and not new_security:
                self.add_non_breaking(
                    "Authentication Removed",
                    f"{location}: Authentication no longer required"
                )

    def compare_collections(self, old_col, new_col):
        """Compare two Postman collections."""
        print("🔍 Analyzing Collection Changes...\n")

        def extract_requests(collection):
            """Extract all requests from collection."""
            requests = {}

            def extract(items, path=""):
                for item in items:
                    if 'request' in item:
                        name = item.get('name', 'Unnamed')
                        full_path = f"{path}/{name}" if path else name

                        request = item['request']
                        method = request.get('method', 'GET')
                        url = request.get('url', {})

                        if isinstance(url, dict):
                            url_str = url.get('raw', '')
                        else:
                            url_str = str(url)

                        requests[full_path] = {
                            'method': method,
                            'url': url_str,
                            'auth': request.get('auth'),
                            'headers': request.get('header', []),
                            'body': request.get('body')
                        }

                    elif 'item' in item:
                        folder = item.get('name', 'Folder')
                        new_path = f"{path}/{folder}" if path else folder
                        extract(item['item'], new_path)

            extract(collection.get('item', []))
            return requests

        old_requests = extract_requests(old_col)
        new_requests = extract_requests(new_col)

        # Check for removed requests
        for name, request in old_requests.items():
            if name not in new_requests:
                self.add_breaking(
                    "Request Removed",
                    f"Request removed: {request['method']} {name}",
                    "critical"
                )
            else:
                new_request = new_requests[name]

                # Check method change
                if request['method'] != new_request['method']:
                    self.add_breaking(
                        "Method Changed",
                        f"{name}: Method changed from {request['method']} to {new_request['method']}",
                        "critical"
                    )

                # Check URL change
                if request['url'] != new_request['url']:
                    self.add_breaking(
                        "URL Changed",
                        f"{name}: URL changed",
                        "high"
                    )

                # Check auth change
                old_auth = request.get('auth', {}).get('type') if request.get('auth') else None
                new_auth = new_request.get('auth', {}).get('type') if new_request.get('auth') else None

                if old_auth != new_auth:
                    if not old_auth and new_auth:
                        self.add_breaking(
                            "Authentication Added",
                            f"{name}: Authentication now required",
                            "high"
                        )
                    elif old_auth and not new_auth:
                        self.add_non_breaking(
                            "Authentication Removed",
                            f"{name}: Authentication removed"
                        )

        # Check for added requests (non-breaking)
        for name in new_requests:
            if name not in old_requests:
                self.add_non_breaking(
                    "Request Added",
                    f"New request: {new_requests[name]['method']} {name}"
                )

    def print_report(self):
        """Print breaking changes report."""
        print("\n" + "=" * 70)
        print("🔴 BREAKING CHANGES REPORT")
        print("=" * 70 + "\n")

        if not self.breaking_changes and not self.non_breaking_changes:
            print("✅ No changes detected\n")
            return

        # Breaking changes
        if self.breaking_changes:
            print(f"🔴 BREAKING CHANGES ({len(self.breaking_changes)}):")
            print("-" * 70)

            # Group by severity
            critical = [c for c in self.breaking_changes if c['severity'] == 'critical']
            high = [c for c in self.breaking_changes if c['severity'] == 'high']

            if critical:
                print("\n⛔ CRITICAL (Will break existing clients):")
                for i, change in enumerate(critical, 1):
                    print(f"{i}. [{change['category']}] {change['message']}")

            if high:
                print("\n🔴 HIGH (May break existing clients):")
                for i, change in enumerate(high, 1):
                    print(f"{i}. [{change['category']}] {change['message']}")

            print()

        # Non-breaking changes
        if self.non_breaking_changes:
            print(f"\n✅ NON-BREAKING CHANGES ({len(self.non_breaking_changes)}):")
            print("-" * 70)
            for i, change in enumerate(self.non_breaking_changes[:10], 1):
                print(f"{i}. [{change['category']}] {change['message']}")

            if len(self.non_breaking_changes) > 10:
                print(f"... and {len(self.non_breaking_changes) - 10} more")
            print()

        # Summary
        print("=" * 70)
        if self.breaking_changes:
            print("⚠️  WARNING: Breaking changes detected!")
            print(f"   {len([c for c in self.breaking_changes if c['severity'] == 'critical'])} critical changes")
            print(f"   {len([c for c in self.breaking_changes if c['severity'] == 'high'])} high-impact changes")
            print("\n💡 Recommendations:")
            print("   • Increment major version (e.g., v1 → v2)")
            print("   • Provide migration guide for consumers")
            print("   • Consider deprecation period")
            print("   • Update API documentation")
        else:
            print("✅ No breaking changes - backward compatible!")
            print("   Safe to deploy as minor/patch version")

        print("=" * 70 + "\n")


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description='Detect breaking changes between API versions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare API versions
  python detect_breaking_changes.py --api <api-id> --old-version <v1-id> --new-version <v2-id>

  # Compare two specs
  python detect_breaking_changes.py --spec <spec-id-1> <spec-id-2>

  # Compare two collections
  python detect_breaking_changes.py --collection <col-id-1> <col-id-2>

  # Compare local files
  python detect_breaking_changes.py --file old.json new.json
        """
    )

    parser.add_argument('--api', metavar='API_ID', help='API ID')
    parser.add_argument('--old-version', metavar='VERSION_ID', help='Old version ID')
    parser.add_argument('--new-version', metavar='VERSION_ID', help='New version ID')
    parser.add_argument('--spec', nargs=2, metavar=('OLD_SPEC', 'NEW_SPEC'), help='Compare two specs')
    parser.add_argument('--collection', nargs=2, metavar=('OLD_COL', 'NEW_COL'), help='Compare two collections')
    parser.add_argument('--file', nargs=2, metavar=('OLD_FILE', 'NEW_FILE'), help='Compare two local files')

    args = parser.parse_args()

    detector = BreakingChangeDetector()

    try:
        if args.api and args.old_version and args.new_version:
            client = PostmanClient()
            print(f"=== Comparing API Versions ===\n")

            # Get old version schema
            old_schemas = client.get_api_schema(args.api, args.old_version)
            old_spec = json.loads(old_schemas[0].get('schema', '{}'))

            # Get new version schema
            new_schemas = client.get_api_schema(args.api, args.new_version)
            new_spec = json.loads(new_schemas[0].get('schema', '{}'))

            detector.compare_openapi_specs(old_spec, new_spec)

        elif args.spec:
            client = PostmanClient()
            print(f"=== Comparing Specs ===\n")

            # Get old spec
            old_spec_data = client.get_spec(args.spec[0])
            old_file = next((f for f in old_spec_data['files'] if f.get('root')), old_spec_data['files'][0])
            old_spec = json.loads(old_file.get('content', '{}'))

            # Get new spec
            new_spec_data = client.get_spec(args.spec[1])
            new_file = next((f for f in new_spec_data['files'] if f.get('root')), new_spec_data['files'][0])
            new_spec = json.loads(new_file.get('content', '{}'))

            detector.compare_openapi_specs(old_spec, new_spec)

        elif args.collection:
            client = PostmanClient()
            print(f"=== Comparing Collections ===\n")

            old_col = client.get_collection(args.collection[0])
            new_col = client.get_collection(args.collection[1])

            detector.compare_collections(old_col, new_col)

        elif args.file:
            print(f"=== Comparing Files ===\n")

            with open(args.file[0], 'r') as f:
                old_spec = json.load(f)

            with open(args.file[1], 'r') as f:
                new_spec = json.load(f)

            detector.compare_openapi_specs(old_spec, new_spec)

        else:
            parser.print_help()
            return

        detector.print_report()

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
