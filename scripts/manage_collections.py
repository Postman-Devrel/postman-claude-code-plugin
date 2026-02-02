#!/usr/bin/env python3
"""
Manage Postman collections: create, update, delete, and get details.
"""

import sys
import os
import json
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.config import PostmanConfig
from scripts.postman_client import PostmanClient


def create_minimal_collection(name, description=""):
    """
    Create a minimal collection structure.

    Args:
        name: Collection name
        description: Collection description

    Returns:
        Dictionary with minimal collection structure
    """
    return {
        "info": {
            "name": name,
            "description": description,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": []
    }


def add_request_to_collection(collection_data, request_name, method, url, description=""):
    """
    Add a request to a collection.

    Args:
        collection_data: Collection dictionary
        request_name: Name of the request
        method: HTTP method (GET, POST, etc.)
        url: Request URL
        description: Request description

    Returns:
        Updated collection data
    """
    request = {
        "name": request_name,
        "request": {
            "method": method,
            "header": [],
            "url": {
                "raw": url,
                "host": url.split("://")[1].split("/")[0].split(".") if "://" in url else [],
                "path": url.split("://")[1].split("/")[1:] if "://" in url and "/" in url.split("://")[1] else []
            },
            "description": description
        }
    }

    collection_data["item"].append(request)
    return collection_data


def main():
    parser = argparse.ArgumentParser(
        description='Manage Postman collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all collections
  python manage_collections.py --list

  # Get collection details
  python manage_collections.py --get <collection-id>

  # Create a new collection
  python manage_collections.py --create --name "My API Tests" --description "API test collection"

  # Create a collection with a request
  python manage_collections.py --create --name "My API" --add-request '{"name": "Get Users", "method": "GET", "url": "https://api.example.com/users"}'

  # Update a collection name
  python manage_collections.py --update <collection-id> --name "New Name"

  # Delete a collection
  python manage_collections.py --delete <collection-id>

  # Duplicate a collection
  python manage_collections.py --duplicate <collection-id> --name "Copy of Collection"
        """
    )

    # Action arguments
    parser.add_argument('--list', action='store_true',
                        help='List all collections')
    parser.add_argument('--get', metavar='COLLECTION_ID',
                        help='Get detailed information about a collection')
    parser.add_argument('--create', action='store_true',
                        help='Create a new collection')
    parser.add_argument('--update', metavar='COLLECTION_ID',
                        help='Update an existing collection')
    parser.add_argument('--delete', metavar='COLLECTION_ID',
                        help='Delete a collection')
    parser.add_argument('--duplicate', metavar='COLLECTION_ID',
                        help='Duplicate an existing collection')

    # Collection data arguments
    parser.add_argument('--name', help='Collection name')
    parser.add_argument('--description', help='Collection description', default='')
    parser.add_argument('--add-request', metavar='REQUEST_JSON',
                        help='Add a request to the collection (JSON format: {"name": "...", "method": "...", "url": "..."})')
    parser.add_argument('--workspace', metavar='WORKSPACE_ID',
                        help='Workspace ID (overrides POSTMAN_WORKSPACE_ID env var)')

    args = parser.parse_args()

    # Validate arguments
    action_count = sum([args.list, bool(args.get), args.create, bool(args.update),
                        bool(args.delete), bool(args.duplicate)])
    if action_count == 0:
        parser.error("Please specify an action: --list, --get, --create, --update, --delete, or --duplicate")
    if action_count > 1:
        parser.error("Please specify only one action at a time")

    try:
        # Initialize client
        config = PostmanConfig()
        if args.workspace:
            config.workspace_id = args.workspace
        client = PostmanClient(config)

        # Execute action
        if args.list:
            print("Fetching collections...")
            collections = client.list_collections()

            if not collections:
                print("\nNo collections found.")
                return

            print(f"\nFound {len(collections)} collection(s):\n")
            for i, collection in enumerate(collections, 1):
                print(f"{i}. {collection.get('name', 'Unnamed')}")
                print(f"   UID: {collection.get('uid', 'N/A')}")
                if collection.get('owner'):
                    print(f"   Owner: {collection['owner']}")
                print()

        elif args.get:
            print(f"Fetching collection details for {args.get}...")
            collection = client.get_collection(args.get)

            print(f"\nCollection: {collection.get('info', {}).get('name', 'Unnamed')}")
            print(f"UID: {collection.get('info', {}).get('_postman_id', 'N/A')}")
            print(f"Schema: {collection.get('info', {}).get('schema', 'N/A')}")

            if collection.get('info', {}).get('description'):
                print(f"\nDescription:\n{collection['info']['description']}")

            items = collection.get('item', [])
            if items:
                print(f"\nRequests ({len(items)}):")
                for item in items:
                    print(f"  - {item.get('name', 'Unnamed')}")
                    if 'request' in item:
                        method = item['request'].get('method', 'N/A')
                        url = item['request'].get('url', {})
                        if isinstance(url, dict):
                            url = url.get('raw', 'N/A')
                        print(f"    {method} {url}")
            else:
                print("\nNo requests in this collection.")

            variables = collection.get('variable', [])
            if variables:
                print(f"\nVariables ({len(variables)}):")
                for var in variables:
                    print(f"  - {var.get('key', 'N/A')}: {var.get('value', 'N/A')}")

        elif args.create:
            if not args.name:
                parser.error("--name is required when creating a collection")

            print(f"Creating collection '{args.name}'...")
            collection_data = create_minimal_collection(args.name, args.description)

            # Add request if specified
            if args.add_request:
                try:
                    request_data = json.loads(args.add_request)
                    collection_data = add_request_to_collection(
                        collection_data,
                        request_data['name'],
                        request_data['method'],
                        request_data['url'],
                        request_data.get('description', '')
                    )
                    print(f"  Added request: {request_data['name']}")
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --add-request: {e}")
                    return 1
                except KeyError as e:
                    print(f"Error: Missing required field in request data: {e}")
                    return 1

            result = client.create_collection(collection_data, workspace_id=args.workspace)

            print(f"\nCollection created successfully!")
            print(f"Name: {result.get('name', 'N/A')}")
            print(f"UID: {result.get('uid', 'N/A')}")

        elif args.update:
            if not args.name:
                parser.error("--name is required when updating a collection")

            print(f"Fetching current collection data...")
            current_collection = client.get_collection(args.update)

            # Update the name
            current_collection['info']['name'] = args.name

            # Update description if provided
            if args.description:
                current_collection['info']['description'] = args.description

            print(f"Updating collection '{args.name}'...")
            result = client.update_collection(args.update, current_collection)

            print(f"\nCollection updated successfully!")
            print(f"Name: {result.get('name', 'N/A')}")
            print(f"UID: {result.get('uid', 'N/A')}")

        elif args.delete:
            print(f"Deleting collection {args.delete}...")

            # Get collection name first
            try:
                collection = client.get_collection(args.delete)
                name = collection.get('info', {}).get('name', args.delete)
            except:
                name = args.delete

            client.delete_collection(args.delete)
            print(f"\nCollection '{name}' deleted successfully!")

        elif args.duplicate:
            if not args.name:
                parser.error("--name is required when duplicating a collection")

            print(f"Fetching collection to duplicate...")
            source_collection = client.get_collection(args.duplicate)

            # Create a new collection data based on the source
            new_collection = {
                "info": {
                    "name": args.name,
                    "description": source_collection.get('info', {}).get('description', ''),
                    "schema": source_collection.get('info', {}).get('schema',
                                                                    'https://schema.getpostman.com/json/collection/v2.1.0/collection.json')
                },
                "item": source_collection.get('item', []),
                "variable": source_collection.get('variable', [])
            }

            print(f"Creating duplicate collection '{args.name}'...")
            result = client.create_collection(new_collection, workspace_id=args.workspace)

            print(f"\nCollection duplicated successfully!")
            print(f"Original: {source_collection.get('info', {}).get('name', 'N/A')} ({args.duplicate})")
            print(f"Duplicate: {result.get('name', 'N/A')} ({result.get('uid', 'N/A')})")

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
