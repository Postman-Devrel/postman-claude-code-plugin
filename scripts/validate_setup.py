#!/usr/bin/env python3
"""
Validates Postman skill setup and provides helpful diagnostics.
Run this first or auto-run on initial skill load.

Usage:
    python validate_setup.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig
from utils.formatters import format_error


def validate_setup():
    """Comprehensive setup validation with helpful output."""

    print("🔍 Validating Postman Skill Setup...\n")

    # 1. Check API key
    config = PostmanConfig()

    if not config.api_key:
        print("❌ No API key found")
        print("📋 Setup: Add POSTMAN_API_KEY to .env file")
        print("🔗 Get key: https://web.postman.co/settings/me/api-keys\n")
        return False

    print(f"✅ API Key found (starts with {config.api_key[:9]}...)\n")

    # 2. Test API connectivity
    print("🌐 Testing Postman API connection...")
    client = PostmanClient(config)

    try:
        # Try to list collections to test connectivity
        collections = client.list_collections()
        print(f"✅ Successfully connected to Postman API\n")
    except Exception as e:
        print(f"❌ API Connection failed: {e}\n")
        print("🔧 Troubleshooting:")
        print("   • Check your API key is valid")
        print("   • Verify network connectivity")
        print("   • Check Postman status: https://status.postman.com/\n")
        return False

    # 3. Check workspace configuration
    if config.workspace_id:
        print(f"📁 Checking configured workspace: {config.workspace_id}")
        try:
            workspace = client.get_workspace(config.workspace_id)
            workspace_name = workspace.get('name', 'Unknown')
            workspace_type = workspace.get('type', 'Unknown')
            print(f"✅ Workspace: {workspace_name} (Type: {workspace_type})\n")

            # 4. Get collection count
            print("📊 Analyzing workspace contents...")
            collections = client.list_collections(config.workspace_id)
            collection_count = len(collections)
            print(f"   Collections: {collection_count}")

            environments = client.list_environments(config.workspace_id)
            environment_count = len(environments)
            print(f"   Environments: {environment_count}")

            try:
                monitors = client.list_monitors(config.workspace_id)
                monitor_count = len(monitors)
                print(f"   Monitors: {monitor_count}")
            except:
                print(f"   Monitors: (unavailable)")

            try:
                apis = client.list_apis(config.workspace_id)
                api_count = len(apis)
                print(f"   APIs: {api_count}\n")
            except:
                print(f"   APIs: (unavailable)\n")

            if collection_count == 0:
                print("ℹ️  This workspace has no collections. You can:")
                print("   • Create a new collection")
                print("   • Switch to a different workspace (run: python scripts/list_workspaces.py)")
                print("   • Import collections from another source\n")

        except Exception as e:
            print(f"⚠️  Workspace issue: {e}")
            print("💡 Try running: python scripts/list_workspaces.py\n")
    else:
        print("ℹ️  No workspace configured (POSTMAN_WORKSPACE_ID not set)")
        print("   Will show all collections across all workspaces")
        print("💡 To set a workspace, add to .env file:")
        print("   POSTMAN_WORKSPACE_ID=your-workspace-id\n")

        try:
            # Try to list collections without workspace filter
            collections = client.list_collections()
            collection_count = len(collections)
            print(f"📊 Total collections (all workspaces): {collection_count}\n")

            if collection_count == 0:
                print("ℹ️  No collections found in any workspace.")
                print("💡 Run: python scripts/list_workspaces.py to see your workspaces\n")
        except Exception as e:
            print(f"⚠️  Could not list collections: {e}\n")

    print("✅ Setup validation complete!\n")
    print("🚀 You're ready to use the Postman skill!")
    print("\n💡 Helpful commands:")
    print("   • List collections: python scripts/list_collections.py")
    print("   • List workspaces: python scripts/list_workspaces.py")
    print("   • List all resources: python scripts/list_collections.py --all\n")

    return True


def main():
    try:
        success = validate_setup()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(format_error(e, "validating setup"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
