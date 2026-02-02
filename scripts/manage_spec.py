#!/usr/bin/env python3
"""
Generic Spec Hub management for OpenAPI and AsyncAPI specifications.

Spec Hub provides direct specification management with support for:
- OpenAPI 3.0 and AsyncAPI 2.0
- Single-file and multi-file specifications
- Bidirectional collection generation
- Better version control integration

Usage:
    python manage_spec.py create --name="My API" --file=openapi.json
    python manage_spec.py list
    python manage_spec.py get --spec-id=<spec-id>
    python manage_spec.py generate-collection --spec-id=<spec-id> --collection-name="My Collection"
    python manage_spec.py --help
"""

import sys
import os
import json
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


def load_spec_file(file_path):
    """Load specification from a file (JSON or YAML)."""
    with open(file_path, 'r') as f:
        content = f.read()

    # Try to detect format
    if file_path.endswith('.yaml') or file_path.endswith('.yml'):
        try:
            import yaml
            # Verify it's valid YAML and return as string
            yaml.safe_load(content)
            return content, 'yaml'
        except ImportError:
            print("Warning: PyYAML not installed. Treating as JSON.")
            return content, 'json'
    else:
        # Verify it's valid JSON
        json.loads(content)
        return content, 'json'


def create_spec(client, name, description, file_path):
    """Create a specification in Spec Hub."""

    print(f"=== Creating Spec: {name} ===\n")

    # Load the spec file
    try:
        spec_content, file_format = load_spec_file(file_path)
        file_name = f"spec.{'yaml' if file_format == 'yaml' else 'json'}"
    except Exception as e:
        print(f"✗ Error loading spec file: {e}")
        return None

    # Prepare spec data
    spec_data = {
        "name": name,
        "description": description or f"API specification: {name}",
        "files": [
            {
                "path": file_name,
                "content": spec_content,
                "root": True
            }
        ]
    }

    try:
        spec = client.create_spec(spec_data)
        spec_id = spec.get('id')
        print(f"✓ Specification created successfully in Spec Hub!")
        print(f"  Spec ID: {spec_id}")
        print(f"  Name: {spec.get('name')}")
        print(f"  Files: {len(spec.get('files', []))}")
        print()
        return spec_id
    except Exception as e:
        print(f"✗ Error creating specification: {e}")
        return None


def get_spec(client, spec_id):
    """Retrieve and display specification details."""

    print(f"=== Getting Spec {spec_id} ===\n")

    try:
        spec = client.get_spec(spec_id)
        files = spec.get('files', [])

        print(f"✓ Specification retrieved successfully!")
        print(f"  Name: {spec.get('name')}")
        print(f"  Description: {spec.get('description')}")
        print(f"  Files: {len(files)}")
        print()

        # Show file details
        for file_obj in files:
            root_marker = "[ROOT] " if file_obj.get('root') else ""
            size = len(file_obj.get('content', ''))
            print(f"    - {root_marker}{file_obj.get('path')} ({size:,} bytes)")

        # Parse and show spec details if JSON
        if files:
            first_file = files[0]
            try:
                spec_parsed = json.loads(first_file.get('content', '{}'))
                print(f"\n  Spec Type: {spec_parsed.get('openapi', spec_parsed.get('asyncapi', 'Unknown'))}")
                if 'info' in spec_parsed:
                    print(f"  Title: {spec_parsed.get('info', {}).get('title')}")
                    print(f"  Version: {spec_parsed.get('info', {}).get('version')}")
                if 'paths' in spec_parsed:
                    print(f"  Endpoints: {len(spec_parsed.get('paths', {}))}")
                if 'components' in spec_parsed:
                    print(f"  Schemas: {len(spec_parsed.get('components', {}).get('schemas', {}))}")
            except:
                pass  # Not JSON or can't parse
        print()
    except Exception as e:
        print(f"✗ Error retrieving specification: {e}")


def list_specs(client, limit=10):
    """List all specifications in workspace."""

    print("=== Listing Specifications ===\n")

    try:
        specs = client.list_specs(limit=limit)
        if not specs:
            print("No specifications found in workspace")
        else:
            print(f"Found {len(specs)} specification(s):")
            for i, s in enumerate(specs, 1):
                print(f"  {i}. {s.get('name')}")
                print(f"     ID: {s.get('id')}")
                if s.get('description'):
                    print(f"     {s.get('description')}")
                print()
    except Exception as e:
        print(f"✗ Error listing specifications: {e}")


def generate_collection_from_spec(client, spec_id, collection_name):
    """Generate a Postman collection from a specification."""

    print(f"=== Generating Collection from Spec {spec_id} ===\n")

    try:
        result = client.generate_collection_from_spec(
            spec_id,
            collection_name=collection_name
        )

        status = result.get('status', 'unknown')
        print(f"✓ Collection generation initiated!")
        print(f"  Status: {status}")

        if status == 'completed' or 'data' in result:
            data = result.get('data', {})
            collection_id = data.get('collectionId')
            if collection_id:
                print(f"  Collection ID: {collection_id}")
                print(f"  Collection Name: {collection_name}")
                print(f"  View in Postman: https://postman.postman.co/collections/{collection_id}")
        elif status == 'pending':
            print(f"  Generation is in progress...")
            print(f"  Check the spec later to see generated collections")
        print()
    except Exception as e:
        print(f"✗ Error generating collection: {e}")
        print("  Note: Collection generation may be asynchronous")


def main():
    """Main workflow for Spec Hub management."""

    parser = argparse.ArgumentParser(
        description='Create and manage API specifications in Postman Spec Hub',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a spec from file
  python manage_spec.py create --name="Payment API" --file=openapi.json

  # List all specs
  python manage_spec.py list

  # Get spec details
  python manage_spec.py get --spec-id=abc-123

  # Generate collection from spec
  python manage_spec.py generate-collection --spec-id=abc-123 --collection-name="My API Collection"
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new specification')
    create_parser.add_argument('--name', required=True, help='Specification name')
    create_parser.add_argument('--description', help='Specification description')
    create_parser.add_argument('--file', required=True, help='Path to OpenAPI/AsyncAPI spec file')

    # List command
    list_parser = subparsers.add_parser('list', help='List all specifications')
    list_parser.add_argument('--limit', type=int, default=10, help='Maximum number of specs to return')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get specification details')
    get_parser.add_argument('--spec-id', required=True, help='Specification ID')

    # Generate collection command
    gen_parser = subparsers.add_parser('generate-collection', help='Generate collection from spec')
    gen_parser.add_argument('--spec-id', required=True, help='Specification ID')
    gen_parser.add_argument('--collection-name', required=True, help='Name for generated collection')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize client
    client = PostmanClient()

    # Execute command
    if args.command == 'create':
        if not os.path.exists(args.file):
            print(f"Error: Spec file not found: {args.file}")
            return

        spec_id = create_spec(client, args.name, args.description, args.file)

        if spec_id:
            print("=== Spec Created Successfully ===")
            print(f"Spec ID: {spec_id}")
            print()
            print("Next Steps:")
            print(f"  - View details: python {sys.argv[0]} get --spec-id {spec_id}")
            print(f"  - Generate collection: python {sys.argv[0]} generate-collection --spec-id {spec_id} --collection-name='My Collection'")
            print(f"  - View in Postman: https://postman.postman.co/workspace/specs")

    elif args.command == 'list':
        list_specs(client, args.limit)

    elif args.command == 'get':
        get_spec(client, args.spec_id)

    elif args.command == 'generate-collection':
        generate_collection_from_spec(client, args.spec_id, args.collection_name)


if __name__ == '__main__':
    main()
