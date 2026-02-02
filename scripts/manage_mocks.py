#!/usr/bin/env python3
"""
Manage Postman mock servers.

Mock servers allow you to simulate API behavior for development and testing.
They can be created from collections and respond with example data.

Usage:
    python manage_mocks.py --list
    python manage_mocks.py --get <mock-id>
    python manage_mocks.py --create --name="My Mock" --collection=<collection-id>
    python manage_mocks.py --delete <mock-id>
    python manage_mocks.py --help
"""

import sys
import os
import argparse
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig
from utils.formatters import format_table, format_json


def list_mocks(client):
    """List all mock servers in workspace."""
    print("=== Mock Servers ===\n")

    try:
        mocks = client.list_mocks()

        if not mocks:
            print("No mock servers found in workspace")
            return

        print(f"Found {len(mocks)} mock server(s):\n")

        for i, mock in enumerate(mocks, 1):
            print(f"{i}. {mock.get('name', 'Unnamed Mock')}")
            print(f"   ID: {mock.get('id')}")
            print(f"   Mock URL: {mock.get('mockUrl', 'N/A')}")
            print(f"   Collection: {mock.get('collection', 'N/A')}")
            if mock.get('environment'):
                print(f"   Environment: {mock.get('environment')}")
            print(f"   Private: {mock.get('private', False)}")
            print()

    except Exception as e:
        print(f"Error listing mock servers: {e}")
        sys.exit(1)


def get_mock(client, mock_id):
    """Get detailed information about a mock server."""
    print(f"=== Mock Server Details ===\n")

    try:
        mock = client.get_mock(mock_id)

        print(f"Name: {mock.get('name', 'Unnamed Mock')}")
        print(f"ID: {mock.get('id')}")
        print(f"Mock URL: {mock.get('mockUrl', 'N/A')}")
        print(f"Collection ID: {mock.get('collection', 'N/A')}")

        if mock.get('environment'):
            print(f"Environment ID: {mock.get('environment')}")

        print(f"Private: {mock.get('private', False)}")

        if mock.get('config'):
            config = mock.get('config', {})
            print(f"\nConfiguration:")
            if config.get('headers'):
                print(f"  Headers: {len(config.get('headers', []))} configured")
            if config.get('delay'):
                print(f"  Delay: {config.get('delay')}ms")

        print(f"\nCreated: {mock.get('createdAt', 'N/A')}")
        print(f"Updated: {mock.get('updatedAt', 'N/A')}")

        print(f"\n📋 Mock URL: {mock.get('mockUrl', 'N/A')}")
        print("   Use this URL to make requests to your mock server")

    except Exception as e:
        print(f"Error getting mock server: {e}")
        sys.exit(1)


def create_mock(client, name, collection_id, environment_id=None, private=False, delay=None):
    """Create a new mock server."""
    print(f"=== Creating Mock Server: {name} ===\n")

    try:
        # Build mock data
        mock_data = {
            "name": name,
            "collection": collection_id,
            "private": private
        }

        if environment_id:
            mock_data["environment"] = environment_id

        if delay is not None:
            mock_data["config"] = {
                "delay": {
                    "type": "fixed",
                    "value": delay
                }
            }

        mock = client.create_mock(mock_data)

        print(f"✓ Mock server created successfully!")
        print(f"  Name: {mock.get('name')}")
        print(f"  ID: {mock.get('id')}")
        print(f"  Mock URL: {mock.get('mockUrl')}")
        print(f"  Collection: {collection_id}")

        if environment_id:
            print(f"  Environment: {environment_id}")

        print(f"  Private: {private}")

        if delay:
            print(f"  Response Delay: {delay}ms")

        print(f"\n📋 Mock URL: {mock.get('mockUrl')}")
        print("   Use this URL to make requests to your mock server")
        print("\nExample:")
        print(f"  curl {mock.get('mockUrl')}/your-endpoint")

    except Exception as e:
        print(f"Error creating mock server: {e}")
        sys.exit(1)


def delete_mock(client, mock_id):
    """Delete a mock server."""
    print(f"=== Deleting Mock Server {mock_id} ===\n")

    try:
        # Get mock details first
        mock = client.get_mock(mock_id)
        print(f"Mock to delete: {mock.get('name', 'Unnamed Mock')}")
        print(f"Mock URL: {mock.get('mockUrl', 'N/A')}\n")

        # Confirm deletion
        response = input("Are you sure you want to delete this mock server? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Deletion cancelled")
            return

        client.delete_mock(mock_id)

        print(f"✓ Mock server deleted successfully!")

    except Exception as e:
        print(f"Error deleting mock server: {e}")
        sys.exit(1)


def update_mock(client, mock_id, name=None, private=None):
    """Update a mock server."""
    print(f"=== Updating Mock Server {mock_id} ===\n")

    try:
        # Build update data
        update_data = {}

        if name:
            update_data["name"] = name

        if private is not None:
            update_data["private"] = private

        if not update_data:
            print("No updates specified. Use --name or --private flags.")
            return

        mock = client.update_mock(mock_id, update_data)

        print(f"✓ Mock server updated successfully!")
        print(f"  Name: {mock.get('name')}")
        print(f"  ID: {mock.get('id')}")
        print(f"  Mock URL: {mock.get('mockUrl')}")
        print(f"  Private: {mock.get('private', False)}")

    except Exception as e:
        print(f"Error updating mock server: {e}")
        sys.exit(1)


def main():
    """Main entry point for mock server management."""

    parser = argparse.ArgumentParser(
        description='Manage Postman mock servers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all mock servers
  python manage_mocks.py --list

  # Get mock server details
  python manage_mocks.py --get abc-123

  # Create a mock server
  python manage_mocks.py --create --name="Payment Mock" --collection=col-456

  # Create a private mock with delay
  python manage_mocks.py --create --name="Test Mock" --collection=col-456 --private --delay=1000

  # Update mock server
  python manage_mocks.py --update abc-123 --name="New Name" --private

  # Delete mock server
  python manage_mocks.py --delete abc-123
        """
    )

    # Operation flags
    parser.add_argument('--list', action='store_true', help='List all mock servers')
    parser.add_argument('--get', metavar='MOCK_ID', help='Get mock server details')
    parser.add_argument('--create', action='store_true', help='Create a new mock server')
    parser.add_argument('--update', metavar='MOCK_ID', help='Update a mock server')
    parser.add_argument('--delete', metavar='MOCK_ID', help='Delete a mock server')

    # Create/Update parameters
    parser.add_argument('--name', help='Mock server name')
    parser.add_argument('--collection', help='Collection ID to mock')
    parser.add_argument('--environment', help='Environment ID (optional)')
    parser.add_argument('--private', action='store_true', help='Make mock server private')
    parser.add_argument('--delay', type=int, help='Response delay in milliseconds')

    args = parser.parse_args()

    # Check if any operation is specified
    if not any([args.list, args.get, args.create, args.update, args.delete]):
        parser.print_help()
        return

    # Initialize client
    client = PostmanClient()

    # Execute operations
    if args.list:
        list_mocks(client)

    elif args.get:
        get_mock(client, args.get)

    elif args.create:
        if not args.name or not args.collection:
            print("Error: --name and --collection are required for creating a mock server")
            parser.print_help()
            sys.exit(1)

        create_mock(
            client,
            args.name,
            args.collection,
            args.environment,
            args.private,
            args.delay
        )

    elif args.update:
        update_mock(client, args.update, args.name, args.private)

    elif args.delete:
        delete_mock(client, args.delete)


if __name__ == '__main__':
    main()
