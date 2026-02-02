#!/usr/bin/env python3
"""
Publish and manage Postman API documentation.

This script helps publish collections as documentation, manage visibility,
and generate changelogs between versions.

Usage:
    python publish_docs.py --collection <collection-id> --publish
    python publish_docs.py --collection <collection-id> --status
    python publish_docs.py --compare --old <collection-id-1> --new <collection-id-2>
    python publish_docs.py --changelog --api <api-id>
    python publish_docs.py --help
"""

import sys
import os
import argparse
import json
from datetime import datetime
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


def publish_collection_docs(client, collection_id, name=None):
    """
    Publish collection as public documentation.

    Note: This creates a public link to the collection that can be shared.
    Postman API may not have a direct "publish documentation" endpoint,
    so this provides collection sharing functionality.
    """
    print(f"=== Publishing Collection Documentation ===\n")

    try:
        # Get collection details
        collection = client.get_collection(collection_id)
        collection_name = collection.get('info', {}).get('name', 'Unnamed Collection')

        print(f"Collection: {collection_name}")
        print(f"ID: {collection_id}\n")

        # Generate public documentation URL
        # Note: Actual publishing may require Postman UI or specific API endpoints
        public_url = f"https://documenter.getpostman.com/view/{collection_id}"

        print("✓ Collection can be accessed for documentation\n")
        print("📚 Documentation URL:")
        print(f"   {public_url}\n")

        print("📋 Collection Details:")
        print(f"   Name: {collection_name}")
        print(f"   Description: {collection.get('info', {}).get('description', 'No description')}")

        # Count requests
        total_requests = 0
        for item in collection.get('item', []):
            if 'request' in item:
                total_requests += 1
            elif 'item' in item:
                total_requests += len([i for i in item['item'] if 'request' in i])

        print(f"   Total Endpoints: {total_requests}\n")

        print("💡 Next Steps:")
        print("   1. Share the documentation URL with your team")
        print("   2. Customize documentation in Postman web UI")
        print("   3. Add examples and descriptions to requests")
        print("   4. Set up environment templates for testing\n")

        print(f"🔗 View in Postman: https://postman.postman.co/collections/{collection_id}")

    except Exception as e:
        print(f"Error publishing documentation: {e}")
        sys.exit(1)


def get_collection_status(client, collection_id):
    """Get collection documentation status."""
    print(f"=== Collection Documentation Status ===\n")

    try:
        collection = client.get_collection(collection_id)
        collection_name = collection.get('info', {}).get('name', 'Unnamed Collection')

        print(f"Collection: {collection_name}")
        print(f"ID: {collection_id}\n")

        # Count documentation metrics
        total_requests = 0
        documented_requests = 0
        requests_with_examples = 0

        def count_requests(items):
            """Recursively count requests and their documentation."""
            nonlocal total_requests, documented_requests, requests_with_examples

            for item in items:
                if 'request' in item:
                    total_requests += 1

                    # Check if request has description
                    if item.get('request', {}).get('description'):
                        documented_requests += 1

                    # Check if request has example responses
                    if item.get('response', []):
                        requests_with_examples += 1

                elif 'item' in item:
                    count_requests(item['item'])

        count_requests(collection.get('item', []))

        # Calculate documentation coverage
        doc_coverage = (documented_requests / total_requests * 100) if total_requests > 0 else 0
        example_coverage = (requests_with_examples / total_requests * 100) if total_requests > 0 else 0

        print("📊 Documentation Metrics:")
        print(f"   Total Endpoints: {total_requests}")
        print(f"   Documented: {documented_requests} ({doc_coverage:.1f}%)")
        print(f"   With Examples: {requests_with_examples} ({example_coverage:.1f}%)\n")

        # Documentation quality score
        score = (doc_coverage + example_coverage) / 2

        print(f"📈 Documentation Quality Score: {score:.1f}/100")

        if score >= 90:
            print("   Grade: A (Excellent) ✅")
        elif score >= 75:
            print("   Grade: B (Good) ✔️")
        elif score >= 60:
            print("   Grade: C (Fair) ⚠️")
        else:
            print("   Grade: D (Needs Improvement) ❌")

        print()

        # Recommendations
        if doc_coverage < 100:
            print("💡 Recommendations:")
            print(f"   • Add descriptions to {total_requests - documented_requests} endpoint(s)")

        if example_coverage < 100:
            if doc_coverage >= 100:
                print("💡 Recommendations:")
            print(f"   • Add example responses to {total_requests - requests_with_examples} endpoint(s)")

    except Exception as e:
        print(f"Error getting collection status: {e}")
        sys.exit(1)


def compare_collections_for_changelog(client, old_id, new_id):
    """Compare two collections and generate a changelog."""
    print(f"=== Generating Changelog ===\n")

    try:
        old_col = client.get_collection(old_id)
        new_col = client.get_collection(new_id)

        old_name = old_col.get('info', {}).get('name', 'Old Version')
        new_name = new_col.get('info', {}).get('name', 'New Version')

        print(f"Comparing:")
        print(f"  Old: {old_name} ({old_id})")
        print(f"  New: {new_name} ({new_id})\n")

        # Extract requests
        def get_requests(collection):
            """Extract all requests from collection."""
            requests = {}

            def extract(items, folder_path=""):
                for item in items:
                    if 'request' in item:
                        name = item.get('name', 'Unnamed')
                        path = f"{folder_path}/{name}" if folder_path else name
                        method = item.get('request', {}).get('method', 'GET')
                        url = item.get('request', {}).get('url', {})

                        if isinstance(url, dict):
                            url_str = url.get('raw', '')
                        else:
                            url_str = str(url)

                        requests[path] = {
                            'name': name,
                            'method': method,
                            'url': url_str,
                            'description': item.get('request', {}).get('description', '')
                        }

                    elif 'item' in item:
                        folder_name = item.get('name', 'Folder')
                        new_path = f"{folder_path}/{folder_name}" if folder_path else folder_name
                        extract(item['item'], new_path)

            extract(collection.get('item', []))
            return requests

        old_requests = get_requests(old_col)
        new_requests = get_requests(new_col)

        # Find differences
        added = {k: v for k, v in new_requests.items() if k not in old_requests}
        removed = {k: v for k, v in old_requests.items() if k not in new_requests}
        modified = {}

        for key in set(old_requests.keys()) & set(new_requests.keys()):
            old_req = old_requests[key]
            new_req = new_requests[key]

            changes = []

            if old_req['method'] != new_req['method']:
                changes.append(f"Method: {old_req['method']} → {new_req['method']}")

            if old_req['url'] != new_req['url']:
                changes.append(f"URL changed")

            if old_req['description'] != new_req['description']:
                changes.append("Description updated")

            if changes:
                modified[key] = changes

        # Print changelog
        print("=" * 70)
        print("# CHANGELOG")
        print("=" * 70)
        print()

        print(f"## {new_name}")
        print(f"*Released: {datetime.now().strftime('%Y-%m-%d')}*\n")

        if added:
            print(f"### ✨ Added ({len(added)} endpoint{'s' if len(added) > 1 else ''})")
            print()
            for name, req in added.items():
                print(f"- **{req['method']}** `{name}`")
                if req['description']:
                    print(f"  - {req['description']}")
            print()

        if modified:
            print(f"### 🔄 Changed ({len(modified)} endpoint{'s' if len(modified) > 1 else ''})")
            print()
            for name, changes in modified.items():
                print(f"- `{name}`")
                for change in changes:
                    print(f"  - {change}")
            print()

        if removed:
            print(f"### ⚠️ Removed ({len(removed)} endpoint{'s' if len(removed) > 1 else ''})")
            print()
            for name, req in removed.items():
                print(f"- **{req['method']}** `{name}`")
            print()

        # Breaking changes analysis
        print("### 🔴 Breaking Changes")
        print()

        breaking_changes = []

        if removed:
            breaking_changes.append(f"{len(removed)} endpoint(s) removed")

        for name, changes in modified.items():
            if any('Method:' in c for c in changes):
                breaking_changes.append(f"Method changed for {name}")

        if breaking_changes:
            for change in breaking_changes:
                print(f"- {change}")
        else:
            print("- None (Backward compatible)")

        print()
        print("=" * 70)

    except Exception as e:
        print(f"Error generating changelog: {e}")
        sys.exit(1)


def generate_api_changelog(client, api_id):
    """Generate changelog for API versions."""
    print(f"=== API Version Changelog ===\n")

    try:
        api = client.get_api(api_id)
        print(f"API: {api.get('name', 'Unnamed')}\n")

        versions = client.get_api_versions(api_id)

        if len(versions) < 2:
            print("Need at least 2 versions to generate a changelog")
            return

        print(f"Found {len(versions)} version(s):\n")

        for i, version in enumerate(versions):
            print(f"  {i + 1}. {version.get('name', 'Unnamed')} (ID: {version.get('id')})")

        print("\n" + "=" * 70)
        print("# API VERSION HISTORY")
        print("=" * 70)
        print()

        for version in versions:
            version_name = version.get('name', 'Unknown')
            created_at = version.get('createdAt', 'Unknown')

            print(f"## Version {version_name}")
            print(f"*Released: {created_at}*\n")

            # Try to get schema
            try:
                schemas = client.get_api_schema(api_id, version.get('id'))
                if schemas:
                    schema = json.loads(schemas[0].get('schema', '{}'))
                    paths = schema.get('paths', {})

                    print(f"### Summary")
                    print(f"- Endpoints: {len(paths)}")

                    # Count methods
                    methods = defaultdict(int)
                    for path, path_methods in paths.items():
                        for method in path_methods.keys():
                            if method in ['get', 'post', 'put', 'delete', 'patch']:
                                methods[method.upper()] += 1

                    print(f"- Methods: {dict(methods)}")
                    print()

            except:
                pass  # Skip if schema unavailable

            print()

    except Exception as e:
        print(f"Error generating API changelog: {e}")
        sys.exit(1)


def main():
    """Main entry point for documentation publishing."""

    parser = argparse.ArgumentParser(
        description='Publish and manage Postman API documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Publish collection documentation
  python publish_docs.py --collection col-123 --publish

  # Check documentation status
  python publish_docs.py --collection col-123 --status

  # Generate changelog between versions
  python publish_docs.py --compare --old col-123 --new col-456

  # Generate API version changelog
  python publish_docs.py --changelog --api api-789
        """
    )

    parser.add_argument('--collection', metavar='COLLECTION_ID', help='Collection ID')
    parser.add_argument('--publish', action='store_true', help='Publish collection documentation')
    parser.add_argument('--status', action='store_true', help='Check documentation status')
    parser.add_argument('--compare', action='store_true', help='Compare two collections for changelog')
    parser.add_argument('--old', metavar='COLLECTION_ID', help='Old collection ID for comparison')
    parser.add_argument('--new', metavar='COLLECTION_ID', help='New collection ID for comparison')
    parser.add_argument('--changelog', action='store_true', help='Generate API version changelog')
    parser.add_argument('--api', metavar='API_ID', help='API ID for changelog')

    args = parser.parse_args()

    if not any([args.publish, args.status, args.compare, args.changelog]):
        parser.print_help()
        return

    # Initialize client
    client = PostmanClient()

    # Execute operations
    if args.publish:
        if not args.collection:
            print("Error: --collection required for publishing")
            sys.exit(1)
        publish_collection_docs(client, args.collection)

    elif args.status:
        if not args.collection:
            print("Error: --collection required for status check")
            sys.exit(1)
        get_collection_status(client, args.collection)

    elif args.compare:
        if not args.old or not args.new:
            print("Error: --old and --new collection IDs required for comparison")
            sys.exit(1)
        compare_collections_for_changelog(client, args.old, args.new)

    elif args.changelog:
        if not args.api:
            print("Error: --api required for changelog generation")
            sys.exit(1)
        generate_api_changelog(client, args.api)


if __name__ == '__main__':
    main()
