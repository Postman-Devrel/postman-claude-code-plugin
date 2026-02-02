#!/usr/bin/env python3
"""
Run a Postman collection using Newman (Postman's CLI collection runner).

This script provides a Python wrapper around Newman to execute Postman collections
and parse the results. Newman must be installed separately via npm.

Prerequisites:
    - Node.js and npm installed
    - Newman installed: npm install -g newman

Usage:
    python run_collection.py --collection="Collection Name"
    python run_collection.py --collection-uid="12345-67890"
    python run_collection.py --collection-uid="12345-67890" --environment-uid="abc-def"
"""

import sys
import os
import argparse
import subprocess
import json
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import get_config
from utils.formatters import format_error


def check_newman_installed():
    """Check if Newman is installed"""
    try:
        result = subprocess.run(
            ['newman', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        return False, None
    except FileNotFoundError:
        return False, None
    except Exception as e:
        return False, str(e)


def find_collection_by_name(client, name):
    """
    Find a collection UID by name.

    Args:
        client: PostmanClient instance
        name: Collection name to search for

    Returns:
        Collection UID if found, None otherwise
    """
    collections = client.list_collections()
    for collection in collections:
        if collection['name'].lower() == name.lower():
            return collection['uid']
    return None


def run_newman(collection_file, environment_file=None, reporters='cli,json', timeout=300):
    """
    Execute Newman with the given collection and environment.

    Args:
        collection_file: Path to collection JSON file
        environment_file: Optional path to environment JSON file
        reporters: Newman reporters to use (default: 'cli,json')
        timeout: Maximum execution time in seconds

    Returns:
        tuple: (success: bool, results: dict)
    """
    cmd = [
        'newman', 'run', collection_file,
        '--reporters', reporters,
        '--reporter-json-export', '/tmp/newman-results.json',
        '--color', 'off',  # Disable colors for easier parsing
        '--disable-unicode'  # Disable unicode for compatibility
    ]

    if environment_file:
        cmd.extend(['--environment', environment_file])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Load JSON results if available
        results = {}
        if os.path.exists('/tmp/newman-results.json'):
            with open('/tmp/newman-results.json', 'r') as f:
                results = json.load(f)

        return result.returncode == 0, results, result.stdout, result.stderr

    except subprocess.TimeoutExpired:
        return False, {}, '', f'Newman execution timed out after {timeout} seconds'
    except Exception as e:
        return False, {}, '', str(e)


def format_test_results(results):
    """
    Format Newman test results for human-readable output.

    Args:
        results: Newman JSON results

    Returns:
        Formatted string
    """
    output = []
    output.append("=" * 60)
    output.append("TEST RESULTS")
    output.append("=" * 60)

    run = results.get('run', {})
    stats = run.get('stats', {})

    # Summary
    output.append("\nSummary:")
    output.append(f"  Total Requests: {stats.get('requests', {}).get('total', 0)}")
    output.append(f"  Requests Failed: {stats.get('requests', {}).get('failed', 0)}")
    output.append(f"  Total Assertions: {stats.get('assertions', {}).get('total', 0)}")
    output.append(f"  Assertions Failed: {stats.get('assertions', {}).get('failed', 0)}")

    # Timings
    timings = run.get('timings', {})
    if timings:
        output.append(f"\n  Total Duration: {timings.get('completed', 0) - timings.get('started', 0)}ms")

    # Failures
    failures = run.get('failures', [])
    if failures:
        output.append(f"\n{len(failures)} Failure(s):")
        for idx, failure in enumerate(failures, 1):
            output.append(f"\n  {idx}. {failure.get('error', {}).get('name', 'Unknown Error')}")
            output.append(f"     Test: {failure.get('error', {}).get('test', 'N/A')}")
            output.append(f"     Message: {failure.get('error', {}).get('message', 'N/A')}")

            # Show which request failed
            source = failure.get('source', {})
            if source:
                output.append(f"     Request: {source.get('name', 'N/A')}")
    else:
        output.append("\n✓ All tests passed!")

    output.append("\n" + "=" * 60)

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description='Run a Postman collection using Newman'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--collection',
        type=str,
        help='Collection name to run'
    )
    group.add_argument(
        '--collection-uid',
        type=str,
        help='Collection UID to run'
    )

    parser.add_argument(
        '--environment',
        type=str,
        help='Environment name to use (optional)'
    )
    parser.add_argument(
        '--environment-uid',
        type=str,
        help='Environment UID to use (optional)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Maximum execution time in seconds (default: 300)'
    )

    args = parser.parse_args()

    try:
        # Check Newman installation
        print("Checking Newman installation...")
        is_installed, version = check_newman_installed()

        if not is_installed:
            print("\n" + format_error(
                "Newman is not installed",
                "running collection tests"
            ))
            print("\nTo install Newman:")
            print("  1. Install Node.js from https://nodejs.org/")
            print("  2. Run: npm install -g newman")
            print("  3. Verify: newman --version")
            sys.exit(1)

        print(f"✓ Newman {version} is installed\n")

        # Get configuration and create client
        config = get_config()
        client = PostmanClient(config)

        # Resolve collection UID
        if args.collection:
            print(f"Finding collection: {args.collection}...")
            collection_uid = find_collection_by_name(client, args.collection)
            if not collection_uid:
                raise ValueError(f"Collection '{args.collection}' not found")
        else:
            collection_uid = args.collection_uid

        print(f"Collection UID: {collection_uid}")

        # Download collection
        print("Downloading collection...")
        collection_data = client.get_collection(collection_uid)

        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            collection_file = f.name
            json.dump(collection_data, f)

        # Handle environment if specified
        environment_file = None
        if args.environment or args.environment_uid:
            print("Downloading environment...")

            if args.environment:
                # Find environment by name
                environments = client.list_environments()
                env_uid = None
                for env in environments:
                    if env['name'].lower() == args.environment.lower():
                        env_uid = env['uid']
                        break
                if not env_uid:
                    raise ValueError(f"Environment '{args.environment}' not found")
            else:
                env_uid = args.environment_uid

            environment_data = client.get_environment(env_uid)

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                environment_file = f.name
                json.dump(environment_data, f)

        # Run Newman
        print(f"\nRunning collection with Newman (timeout: {args.timeout}s)...")
        print("-" * 60)

        success, results, stdout, stderr = run_newman(
            collection_file,
            environment_file,
            timeout=args.timeout
        )

        # Print Newman console output
        if stdout:
            print(stdout)

        # Format and print results
        if results:
            print(format_test_results(results))

        # Print any errors
        if stderr:
            print("\nNewman Errors:", file=sys.stderr)
            print(stderr, file=sys.stderr)

        # Cleanup
        os.unlink(collection_file)
        if environment_file:
            os.unlink(environment_file)
        if os.path.exists('/tmp/newman-results.json'):
            os.unlink('/tmp/newman-results.json')

        sys.exit(0 if success else 1)

    except Exception as e:
        print(format_error(e, "running collection"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
