#!/usr/bin/env python3
"""
Generic collection-based API workflow management.

Demonstrates Design phase workflow using collections as the primary artifact.
Collections can be created from scratch, imported from OpenAPI, or duplicated.

Usage:
    python manage_collection_workflow.py create --name="My API" --description="API description"
    python manage_collection_workflow.py import --name="My API" --spec-file=openapi.json
    python manage_collection_workflow.py duplicate --collection-id=<id> --new-name="Copy"
    python manage_collection_workflow.py compare --id1=<id1> --id2=<id2>
    python manage_collection_workflow.py --help
"""

import sys
import os
import json
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


def create_basic_collection(name, description, base_url="https://api.example.com"):
    """Create a basic Postman collection structure."""
    return {
        "info": {
            "name": name,
            "description": description,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": base_url,
                "type": "string"
            }
        ],
        "item": []
    }


def openapi_to_collection(spec_data, collection_name):
    """Convert OpenAPI specification to Postman collection structure."""

    # Get base URL from servers
    base_url = "https://api.example.com"
    if 'servers' in spec_data and spec_data['servers']:
        base_url = spec_data['servers'][0].get('url', base_url)

    collection = {
        "info": {
            "name": collection_name,
            "description": spec_data.get('info', {}).get('description', ''),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "baseUrl",
                "value": base_url,
                "type": "string"
            }
        ],
        "item": []
    }

    # Convert paths to collection items
    for path, methods in spec_data.get('paths', {}).items():
        for method, operation in methods.items():
            if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                continue

            # Build request
            request = {
                "name": operation.get('summary', f"{method.upper()} {path}"),
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": f"{{{{baseUrl}}}}{path}",
                        "host": ["{{baseUrl}}"],
                        "path": [p for p in path.split('/') if p]
                    },
                    "description": operation.get('description', '')
                },
                "response": []
            }

            # Add query parameters
            if 'parameters' in operation:
                query = []
                for param in operation['parameters']:
                    if param.get('in') == 'query':
                        query.append({
                            "key": param.get('name'),
                            "value": "",
                            "description": param.get('description', '')
                        })
                if query:
                    request['request']['url']['query'] = query

            # Add request body if present
            if 'requestBody' in operation:
                request['request']['header'].append({
                    "key": "Content-Type",
                    "value": "application/json"
                })
                request['request']['body'] = {
                    "mode": "raw",
                    "raw": "{}"
                }

            collection['item'].append(request)

    return collection


def compare_collections(client, id1, id2):
    """Compare two collections and identify differences."""

    print(f"=== Comparing Collections ===\n")

    try:
        col1 = client.get_collection(id1)
        col2 = client.get_collection(id2)

        name1 = col1.get('info', {}).get('name', 'Collection 1')
        name2 = col2.get('info', {}).get('name', 'Collection 2')

        # Count requests
        def count_requests(collection):
            count = 0
            for item in collection.get('item', []):
                if 'request' in item:
                    count += 1
                elif 'item' in item:  # Folder
                    count += len([i for i in item['item'] if 'request' in i])
            return count

        count1 = count_requests(col1)
        count2 = count_requests(col2)

        # Extract request names
        def get_request_names(collection):
            names = []
            for item in collection.get('item', []):
                if 'request' in item:
                    names.append(item.get('name'))
                elif 'item' in item:  # Folder
                    names.extend([i.get('name') for i in item['item'] if 'request' in i])
            return names

        names1 = set(get_request_names(col1))
        names2 = set(get_request_names(col2))

        added = names2 - names1
        removed = names1 - names2
        common = names1 & names2

        print(f"Collection 1: {name1}")
        print(f"  ID: {id1}")
        print(f"  Requests: {count1}")
        print()

        print(f"Collection 2: {name2}")
        print(f"  ID: {id2}")
        print(f"  Requests: {count2}")
        print()

        print("=== Differences ===")
        print()

        if added:
            print(f"✓ Added in Collection 2 ({len(added)} requests):")
            for name in sorted(added):
                print(f"  + {name}")
            print()

        if removed:
            print(f"⚠ Removed from Collection 1 ({len(removed)} requests):")
            for name in sorted(removed):
                print(f"  - {name}")
            print()

        if common:
            print(f"Unchanged: {len(common)} requests appear in both collections")
            print()

        # Breaking changes analysis
        if not removed:
            print("✓ No breaking changes - all Collection 1 requests preserved")
        else:
            print("⚠ Breaking changes detected - removed requests may affect workflows")

    except Exception as e:
        print(f"✗ Error comparing collections: {e}")


def main():
    """Main workflow for collection management."""

    parser = argparse.ArgumentParser(
        description='Create and manage Postman collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a basic collection
  python manage_collection_workflow.py create --name="My API" --description="API description"

  # Import collection from OpenAPI spec
  python manage_collection_workflow.py import --name="My API" --spec-file=openapi.json

  # Duplicate a collection
  python manage_collection_workflow.py duplicate --collection-id=abc-123 --new-name="Copy"

  # Compare two collections
  python manage_collection_workflow.py compare --id1=abc-123 --id2=def-456
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a basic collection')
    create_parser.add_argument('--name', required=True, help='Collection name')
    create_parser.add_argument('--description', required=True, help='Collection description')
    create_parser.add_argument('--base-url', default='https://api.example.com', help='Base URL for API')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import collection from OpenAPI spec')
    import_parser.add_argument('--name', required=True, help='Collection name')
    import_parser.add_argument('--spec-file', required=True, help='Path to OpenAPI spec file')

    # Duplicate command
    dup_parser = subparsers.add_parser('duplicate', help='Duplicate an existing collection')
    dup_parser.add_argument('--collection-id', required=True, help='Collection ID to duplicate')
    dup_parser.add_argument('--new-name', required=True, help='Name for duplicated collection')

    # Compare command
    cmp_parser = subparsers.add_parser('compare', help='Compare two collections')
    cmp_parser.add_argument('--id1', required=True, help='First collection ID')
    cmp_parser.add_argument('--id2', required=True, help='Second collection ID')

    # List command
    list_parser = subparsers.add_parser('list', help='List all collections')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize client
    client = PostmanClient()

    # Execute command
    if args.command == 'create':
        print(f"=== Creating Collection: {args.name} ===\n")

        collection = create_basic_collection(args.name, args.description, args.base_url)

        try:
            result = client.create_collection(collection)
            collection_id = result.get('uid')
            print(f"✓ Collection created successfully!")
            print(f"  ID: {collection_id}")
            print(f"  Name: {result.get('name')}")
            print()
            print("Note: This is a basic empty collection.")
            print("Add requests manually in Postman or use 'import' command to create from OpenAPI spec.")
            print()
            print(f"View in Postman: https://postman.postman.co/collections/{collection_id}")
        except Exception as e:
            print(f"✗ Error creating collection: {e}")

    elif args.command == 'import':
        print(f"=== Importing Collection from OpenAPI Spec ===\n")

        if not os.path.exists(args.spec_file):
            print(f"Error: Spec file not found: {args.spec_file}")
            return

        try:
            # Load spec
            with open(args.spec_file, 'r') as f:
                if args.spec_file.endswith('.yaml') or args.spec_file.endswith('.yml'):
                    try:
                        import yaml
                        spec_data = yaml.safe_load(f)
                    except ImportError:
                        print("Error: PyYAML not installed. Install with: pip install pyyaml")
                        return
                else:
                    spec_data = json.load(f)

            # Convert to collection
            collection = openapi_to_collection(spec_data, args.name)

            # Create collection
            result = client.create_collection(collection)
            collection_id = result.get('uid')
            print(f"✓ Collection imported successfully!")
            print(f"  ID: {collection_id}")
            print(f"  Name: {result.get('name')}")
            print(f"  Requests: {len(collection['item'])}")
            print()
            print(f"View in Postman: https://postman.postman.co/collections/{collection_id}")
        except Exception as e:
            print(f"✗ Error importing collection: {e}")

    elif args.command == 'duplicate':
        print(f"=== Duplicating Collection ===\n")

        try:
            result = client.duplicate_collection(args.collection_id, args.new_name)
            new_id = result.get('uid')
            print(f"✓ Collection duplicated successfully!")
            print(f"  Original ID: {args.collection_id}")
            print(f"  New ID: {new_id}")
            print(f"  New Name: {args.new_name}")
            print()
            print(f"View in Postman: https://postman.postman.co/collections/{new_id}")
        except Exception as e:
            print(f"✗ Error duplicating collection: {e}")

    elif args.command == 'compare':
        compare_collections(client, args.id1, args.id2)

    elif args.command == 'list':
        print("=== Listing Collections ===\n")
        try:
            collections = client.list_collections()
            if not collections:
                print("No collections found in workspace")
            else:
                print(f"Found {len(collections)} collection(s):")
                for i, col in enumerate(collections, 1):
                    print(f"  {i}. {col.get('name')} (ID: {col.get('uid')})")
        except Exception as e:
            print(f"✗ Error listing collections: {e}")


if __name__ == '__main__':
    main()
