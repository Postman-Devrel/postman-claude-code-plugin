#!/usr/bin/env python3
"""
Manage Postman environments: create, update, delete, and get details.
"""

import sys
import os
import json
import argparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.config import PostmanConfig
from scripts.postman_client import PostmanClient


def create_minimal_environment(name, values=None):
    """
    Create a minimal environment structure.

    Args:
        name: Environment name
        values: List of environment variables (dicts with key, value, type, enabled)

    Returns:
        Dictionary with minimal environment structure
    """
    return {
        "name": name,
        "values": values or []
    }


def add_variable_to_environment(environment_data, key, value, var_type="default", enabled=True):
    """
    Add a variable to an environment.

    Args:
        environment_data: Environment dictionary
        key: Variable key/name
        value: Variable value
        var_type: Variable type (default, secret)
        enabled: Whether the variable is enabled

    Returns:
        Updated environment data
    """
    variable = {
        "key": key,
        "value": value,
        "type": var_type,
        "enabled": enabled
    }

    environment_data["values"].append(variable)
    return environment_data


def main():
    parser = argparse.ArgumentParser(
        description='Manage Postman environments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all environments
  python manage_environments.py --list

  # Get environment details
  python manage_environments.py --get <environment-id>

  # Create a new environment
  python manage_environments.py --create --name "Development"

  # Create an environment with variables
  python manage_environments.py --create --name "Dev" --add-var '{"key": "API_URL", "value": "https://dev.api.com"}'

  # Add multiple variables (as JSON array)
  python manage_environments.py --create --name "Staging" --variables '[{"key":"API_URL","value":"https://staging.api.com"},{"key":"API_KEY","value":"secret123","type":"secret"}]'

  # Update an environment name
  python manage_environments.py --update <environment-id> --name "New Name"

  # Delete an environment
  python manage_environments.py --delete <environment-id>

  # Duplicate an environment
  python manage_environments.py --duplicate <environment-id> --name "Copy of Environment"
        """
    )

    # Action arguments
    parser.add_argument('--list', action='store_true',
                        help='List all environments')
    parser.add_argument('--get', metavar='ENVIRONMENT_ID',
                        help='Get detailed information about an environment')
    parser.add_argument('--create', action='store_true',
                        help='Create a new environment')
    parser.add_argument('--update', metavar='ENVIRONMENT_ID',
                        help='Update an existing environment')
    parser.add_argument('--delete', metavar='ENVIRONMENT_ID',
                        help='Delete an environment')
    parser.add_argument('--duplicate', metavar='ENVIRONMENT_ID',
                        help='Duplicate an existing environment')

    # Environment data arguments
    parser.add_argument('--name', help='Environment name')
    parser.add_argument('--add-var', metavar='VARIABLE_JSON',
                        help='Add a variable (JSON format: {"key": "...", "value": "...", "type": "default|secret"})')
    parser.add_argument('--variables', metavar='VARIABLES_JSON',
                        help='Add multiple variables (JSON array format)')
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
            print("Fetching environments...")
            environments = client.list_environments()

            if not environments:
                print("\nNo environments found.")
                return

            print(f"\nFound {len(environments)} environment(s):\n")
            for i, env in enumerate(environments, 1):
                print(f"{i}. {env.get('name', 'Unnamed')}")
                print(f"   UID: {env.get('uid', 'N/A')}")
                if env.get('owner'):
                    print(f"   Owner: {env['owner']}")
                print()

        elif args.get:
            print(f"Fetching environment details for {args.get}...")
            environment = client.get_environment(args.get)

            print(f"\nEnvironment: {environment.get('name', 'Unnamed')}")
            print(f"UID: {environment.get('uid', 'N/A')}")

            values = environment.get('values', [])
            if values:
                print(f"\nVariables ({len(values)}):")
                for var in values:
                    key = var.get('key', 'N/A')
                    value = var.get('value', 'N/A')
                    var_type = var.get('type', 'default')
                    enabled = var.get('enabled', True)

                    # Mask secret values
                    if var_type == 'secret':
                        value = '********'

                    status = '✓' if enabled else '✗'
                    type_indicator = ' [secret]' if var_type == 'secret' else ''
                    print(f"  {status} {key}: {value}{type_indicator}")
            else:
                print("\nNo variables in this environment.")

        elif args.create:
            if not args.name:
                parser.error("--name is required when creating an environment")

            print(f"Creating environment '{args.name}'...")
            environment_data = create_minimal_environment(args.name)

            # Add single variable if specified
            if args.add_var:
                try:
                    var_data = json.loads(args.add_var)
                    environment_data = add_variable_to_environment(
                        environment_data,
                        var_data['key'],
                        var_data['value'],
                        var_data.get('type', 'default'),
                        var_data.get('enabled', True)
                    )
                    print(f"  Added variable: {var_data['key']}")
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --add-var: {e}")
                    return 1
                except KeyError as e:
                    print(f"Error: Missing required field in variable data: {e}")
                    return 1

            # Add multiple variables if specified
            if args.variables:
                try:
                    variables = json.loads(args.variables)
                    if not isinstance(variables, list):
                        print("Error: --variables must be a JSON array")
                        return 1

                    for var_data in variables:
                        environment_data = add_variable_to_environment(
                            environment_data,
                            var_data['key'],
                            var_data['value'],
                            var_data.get('type', 'default'),
                            var_data.get('enabled', True)
                        )
                        print(f"  Added variable: {var_data['key']}")
                except json.JSONDecodeError as e:
                    print(f"Error: Invalid JSON in --variables: {e}")
                    return 1
                except KeyError as e:
                    print(f"Error: Missing required field in variable data: {e}")
                    return 1

            result = client.create_environment(environment_data, workspace_id=args.workspace)

            print(f"\nEnvironment created successfully!")
            print(f"Name: {result.get('name', 'N/A')}")
            print(f"UID: {result.get('uid', 'N/A')}")

        elif args.update:
            if not args.name:
                parser.error("--name is required when updating an environment")

            print(f"Fetching current environment data...")
            current_environment = client.get_environment(args.update)

            # Update the name
            current_environment['name'] = args.name

            print(f"Updating environment '{args.name}'...")
            result = client.update_environment(args.update, current_environment)

            print(f"\nEnvironment updated successfully!")
            print(f"Name: {result.get('name', 'N/A')}")
            print(f"UID: {result.get('uid', 'N/A')}")

        elif args.delete:
            print(f"Deleting environment {args.delete}...")

            # Get environment name first
            try:
                environment = client.get_environment(args.delete)
                name = environment.get('name', args.delete)
            except:
                name = args.delete

            client.delete_environment(args.delete)
            print(f"\nEnvironment '{name}' deleted successfully!")

        elif args.duplicate:
            if not args.name:
                parser.error("--name is required when duplicating an environment")

            print(f"Fetching environment to duplicate...")
            source_environment = client.get_environment(args.duplicate)

            # Create a new environment data based on the source
            new_environment = {
                "name": args.name,
                "values": source_environment.get('values', [])
            }

            print(f"Creating duplicate environment '{args.name}'...")
            result = client.create_environment(new_environment, workspace_id=args.workspace)

            print(f"\nEnvironment duplicated successfully!")
            print(f"Original: {source_environment.get('name', 'N/A')} ({args.duplicate})")
            print(f"Duplicate: {result.get('name', 'N/A')} ({result.get('uid', 'N/A')})")

        return 0

    except Exception as e:
        print(f"\nError: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
