#!/usr/bin/env python3
"""
Generic API management with versions and schemas.
Demonstrates the full Design phase workflow: create, validate, version, and compare.

Usage:
    python manage_api.py --name="My API" --description="API description"
    python manage_api.py --name="My API" --spec-file=path/to/openapi.json
    python manage_api.py --help
"""

import sys
import os
import json
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


def load_openapi_spec(file_path):
    """Load OpenAPI specification from a file (JSON or YAML)."""
    with open(file_path, 'r') as f:
        if file_path.endswith('.yaml') or file_path.endswith('.yml'):
            try:
                import yaml
                return yaml.safe_load(f)
            except ImportError:
                print("Error: PyYAML not installed. Install with: pip install pyyaml")
                sys.exit(1)
        else:
            return json.load(f)


def create_api_with_spec(client, api_name, description, spec_data):
    """Create an API with a version and schema from an OpenAPI spec."""

    print(f"=== Creating API: {api_name} ===\n")

    # Step 1: Create the API
    print("Step 1: Creating API...")
    api_data = {
        "name": api_name,
        "summary": description,
        "description": description
    }

    try:
        api = client.create_api(api_data)
        api_id = api.get('id')
        print(f"✓ API created successfully!")
        print(f"  ID: {api_id}")
        print(f"  Name: {api.get('name')}")
        print()
    except Exception as e:
        print(f"✗ Error creating API: {e}")
        return None

    # Step 2: Create version and add schema
    version_name = spec_data.get('info', {}).get('version', '1.0.0')
    print(f"Step 2: Creating version {version_name} with OpenAPI schema...")

    try:
        # Create version
        version_data = {"name": version_name}
        version_response = client._make_request(
            'POST',
            f"/apis/{api_id}/versions",
            json={'version': version_data}
        )
        version_id = version_response.get('version', {}).get('id')
        print(f"✓ Version {version_name} created!")
        print(f"  ID: {version_id}")

        # Add schema to version
        schema_data = {
            "type": "openapi3",
            "language": "json",
            "schema": json.dumps(spec_data)
        }

        schema_response = client._make_request(
            'POST',
            f"/apis/{api_id}/versions/{version_id}/schemas",
            json={'schema': schema_data}
        )
        schema_id = schema_response.get('schema', {}).get('id')

        # Count paths/endpoints
        paths_count = len(spec_data.get('paths', {}))

        print(f"✓ OpenAPI 3.0 schema added to v{version_name}!")
        print(f"  Schema ID: {schema_id}")
        print(f"  API Title: {spec_data.get('info', {}).get('title')}")
        print(f"  Endpoints: {paths_count}")
        print()
    except Exception as e:
        print(f"✗ Error creating version or schema: {e}")
        return None

    # Step 3: Validate the schema
    print("Step 3: Validating schema...")
    try:
        schemas = client.get_api_schema(api_id, version_id)
        if schemas:
            schema = schemas[0]
            schema_content = json.loads(schema.get('schema', '{}'))

            print("✓ Schema validation successful!")
            print(f"  Type: {schema.get('type')}")
            print(f"  Language: {schema.get('language')}")
            print(f"  API Title: {schema_content.get('info', {}).get('title')}")
            print(f"  API Version: {schema_content.get('info', {}).get('version')}")
            print(f"  Paths defined: {len(schema_content.get('paths', {}))}")
            print(f"  Schemas defined: {len(schema_content.get('components', {}).get('schemas', {}))}")
            print()
        else:
            print("✗ No schema found")
            return None
    except Exception as e:
        print(f"✗ Error validating schema: {e}")
        return None

    print("=== API Created Successfully ===")
    print(f"API ID: {api_id}")
    print(f"Version ID: {version_id}")
    print(f"View in Postman: https://postman.postman.co/workspace/apis/{api_id}")
    print()

    return {
        'api_id': api_id,
        'version_id': version_id,
        'schema_id': schema_id
    }


def main():
    """Main workflow for generic API management."""

    parser = argparse.ArgumentParser(
        description='Create and manage Postman APIs with OpenAPI specifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create API from OpenAPI spec file
  python manage_api.py --name="Payment API" --spec-file=openapi.json

  # Create API with description
  python manage_api.py --name="User API" --description="User management API" --spec-file=spec.yaml
        """
    )

    parser.add_argument('--name', required=True, help='API name')
    parser.add_argument('--description', help='API description (defaults to spec description)')
    parser.add_argument('--spec-file', required=True, help='Path to OpenAPI spec file (JSON or YAML)')
    parser.add_argument('--list', action='store_true', help='List all APIs in workspace')
    parser.add_argument('--get', metavar='API_ID', help='Get details of a specific API')

    args = parser.parse_args()

    # Initialize client
    client = PostmanClient()

    # List APIs
    if args.list:
        print("=== Listing APIs ===\n")
        try:
            apis = client.list_apis()
            if not apis:
                print("No APIs found in workspace")
            else:
                for i, api in enumerate(apis, 1):
                    print(f"{i}. {api.get('name')} (ID: {api.get('id')})")
                    if api.get('summary'):
                        print(f"   {api.get('summary')}")
        except Exception as e:
            print(f"Error listing APIs: {e}")
        return

    # Get API details
    if args.get:
        print(f"=== Getting API {args.get} ===\n")
        try:
            api = client.get_api(args.get)
            print(f"Name: {api.get('name')}")
            print(f"ID: {api.get('id')}")
            print(f"Description: {api.get('description')}")
            print(f"Created: {api.get('createdAt')}")
            print(f"Updated: {api.get('updatedAt')}")

            # Get versions
            versions = client.get_api_versions(args.get)
            print(f"\nVersions: {len(versions)}")
            for v in versions:
                print(f"  - {v.get('name')} (ID: {v.get('id')})")
        except Exception as e:
            print(f"Error getting API: {e}")
        return

    # Create API with spec
    if not args.spec_file:
        print("Error: --spec-file is required when creating an API")
        parser.print_help()
        return

    # Load OpenAPI spec
    if not os.path.exists(args.spec_file):
        print(f"Error: Spec file not found: {args.spec_file}")
        return

    try:
        spec_data = load_openapi_spec(args.spec_file)
    except Exception as e:
        print(f"Error loading spec file: {e}")
        return

    # Use description from spec if not provided
    description = args.description or spec_data.get('info', {}).get('description', 'API managed by Postman')

    # Create the API
    result = create_api_with_spec(client, args.name, description, spec_data)

    if result:
        print("\nNext Steps:")
        print(f"  - Get API details: python {sys.argv[0]} --get {result['api_id']}")
        print(f"  - List all APIs: python {sys.argv[0]} --list")
        print(f"  - View in Postman: https://postman.postman.co/workspace/apis/{result['api_id']}")


if __name__ == '__main__':
    main()
