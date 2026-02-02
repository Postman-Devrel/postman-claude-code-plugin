#!/usr/bin/env python3
"""
List all accessible Postman workspaces with collection counts.

Usage:
    python list_workspaces.py
    python list_workspaces.py --detailed  # Show more info for each workspace
"""

import sys
import os
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import get_config
from utils.formatters import format_error


def list_workspaces(detailed=False):
    """
    List all accessible workspaces.

    Args:
        detailed: If True, show additional details for each workspace
    """
    config = get_config()
    client = PostmanClient(config)

    print("📂 Your Postman Workspaces:\n")

    try:
        # Get all workspaces
        # Note: Postman API doesn't have a direct /workspaces endpoint for listing all
        # We'll need to use a workaround by getting workspace info

        # First, try to get current workspace if configured
        workspaces = []

        if config.workspace_id:
            try:
                workspace = client.get_workspace(config.workspace_id)
                workspaces.append(workspace)
            except Exception as e:
                print(f"⚠️  Could not fetch configured workspace: {e}\n")

        # If we don't have workspaces, we can't list them directly via API
        # The Postman API requires knowing workspace IDs to get workspace info
        if not workspaces:
            print("ℹ️  Workspace listing requires the Postman API to support workspace enumeration.")
            print("   Currently, you need to know the workspace ID to access it.\n")
            print("💡 To use a specific workspace:")
            print("   1. Find your workspace ID from the Postman web app URL")
            print("      (e.g., https://web.postman.co/workspace/YOUR-WORKSPACE-ID)")
            print("   2. Add to .env file: POSTMAN_WORKSPACE_ID=YOUR-WORKSPACE-ID\n")
            print("🔗 Access workspaces: https://web.postman.co/home\n")
            return

        # Display workspace information
        for i, ws in enumerate(workspaces, 1):
            is_current = "⭐" if ws.get('id') == config.workspace_id else "  "
            print(f"{is_current} {i}. {ws.get('name', 'Unknown')}")
            print(f"      Type: {ws.get('type', 'Unknown')} | ID: {ws.get('id', 'Unknown')}")

            if detailed:
                print(f"      Description: {ws.get('description', 'No description')}")

            # Show resource counts
            try:
                collections = client.list_collections(ws.get('id'))
                collection_count = len(collections)
                print(f"      📊 Collections: {collection_count}")

                if detailed:
                    environments = client.list_environments(ws.get('id'))
                    print(f"      🌍 Environments: {len(environments)}")

                    try:
                        monitors = client.list_monitors(ws.get('id'))
                        print(f"      📈 Monitors: {len(monitors)}")
                    except:
                        pass

                    try:
                        apis = client.list_apis(ws.get('id'))
                        print(f"      🔌 APIs: {len(apis)}")
                    except:
                        pass

            except Exception as e:
                print(f"      ⚠️  Could not fetch resource counts: {e}")

            print()

        print("\n💡 To switch workspace:")
        print("   Edit POSTMAN_WORKSPACE_ID in your .env file\n")

    except Exception as e:
        raise Exception(f"Failed to list workspaces: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='List all accessible Postman workspaces'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed information for each workspace'
    )

    args = parser.parse_args()

    try:
        list_workspaces(detailed=args.detailed)
    except Exception as e:
        print(format_error(e, "listing workspaces"), file=sys.stderr)
        print("\n🔧 Troubleshooting:")
        print("   • Run: python scripts/validate_setup.py")
        print("   • Check: https://status.postman.com/")
        print("   • Verify your API key has workspace access\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
