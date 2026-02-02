#!/usr/bin/env python3
"""
List Postman workspace resources (collections, environments, monitors, APIs).

Usage:
    python list_collections.py                    # List collections
    python list_collections.py --all              # List all resources
    python list_collections.py --environments     # List environments
    python list_collections.py --monitors         # List monitors
    python list_collections.py --apis             # List APIs
"""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import get_config
from utils.formatters import (
    format_collections_list,
    format_environments_list,
    format_monitors_list,
    format_apis_list,
    format_workspace_summary,
    format_error
)


def main():
    parser = argparse.ArgumentParser(
        description='List Postman workspace resources'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='List all resource types'
    )
    parser.add_argument(
        '--environments',
        action='store_true',
        help='List environments'
    )
    parser.add_argument(
        '--monitors',
        action='store_true',
        help='List monitors'
    )
    parser.add_argument(
        '--apis',
        action='store_true',
        help='List APIs'
    )
    parser.add_argument(
        '--workspace',
        type=str,
        help='Workspace ID (optional, uses POSTMAN_WORKSPACE_ID env var if not provided)'
    )

    args = parser.parse_args()

    try:
        # Get configuration
        config = get_config()

        # Override workspace if provided
        if args.workspace:
            config.workspace_id = args.workspace

        # Create client
        client = PostmanClient(config)

        # Determine what to list
        if args.all:
            # List everything for workspace summary
            print("Fetching workspace resources...")
            collections = client.list_collections()
            environments = client.list_environments()
            monitors = client.list_monitors()
            apis = client.list_apis()

            print(format_workspace_summary(collections, environments, monitors, apis))

        elif args.environments:
            print("Fetching environments...")
            environments = client.list_environments()
            print(format_environments_list(environments))

        elif args.monitors:
            print("Fetching monitors...")
            monitors = client.list_monitors()
            print(format_monitors_list(monitors))

        elif args.apis:
            print("Fetching APIs...")
            apis = client.list_apis()
            print(format_apis_list(apis))

        else:
            # Default: list collections

            # Show workspace context if configured
            if config.workspace_id:
                try:
                    workspace = client.get_workspace(config.workspace_id)
                    workspace_name = workspace.get('name', 'Unknown')
                    print(f"📁 Workspace: {workspace_name}\n")
                except:
                    pass  # Continue even if workspace fetch fails

            print("Fetching collections...")
            collections = client.list_collections()

            if len(collections) == 0:
                print("\n📭 No collections found in this workspace.")
                print("\n💡 Quick actions:")
                if config.workspace_id:
                    print("   • List workspaces: python scripts/list_workspaces.py")
                    print("   • Change workspace: Edit POSTMAN_WORKSPACE_ID in .env")
                print("   • Run setup validation: python scripts/validate_setup.py")
            else:
                print(format_collections_list(collections))

    except Exception as e:
        print(format_error(e, "listing workspace resources"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
