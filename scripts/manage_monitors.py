#!/usr/bin/env python3
"""
Manage Postman Monitors - Create, Update, Delete, and Analyze
Part of Phase 6: Observe - Monitor Operations
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.config import get_config
from scripts.postman_client import PostmanClient
from utils.formatters import format_error


def list_monitors(client, verbose=False):
    """List all monitors in the workspace"""
    try:
        monitors = client.list_monitors()

        if not monitors:
            print("No monitors found in this workspace.")
            return

        print(f"Found {len(monitors)} monitor(s)")
        print("=" * 80)
        print()

        for monitor in monitors:
            status = "✓ Active" if monitor.get('active', False) else "✗ Inactive"
            print(f"{status} {monitor.get('name', 'Unnamed Monitor')}")
            print(f"   ID: {monitor.get('id')}")
            print(f"   UID: {monitor.get('uid')}")

            if verbose:
                if monitor.get('collectionUid'):
                    print(f"   Collection: {monitor.get('collectionUid')}")
                if monitor.get('environmentUid'):
                    print(f"   Environment: {monitor.get('environmentUid')}")
                if monitor.get('schedule'):
                    schedule = monitor.get('schedule', {})
                    print(f"   Schedule: {schedule.get('cron', 'Not set')}")
                if monitor.get('lastRun'):
                    print(f"   Last Run: {monitor.get('lastRun', {}).get('finishedAt', 'Never')}")

            print()

    except Exception as e:
        print(format_error("listing monitors", e))
        sys.exit(1)


def get_monitor_details(client, monitor_id):
    """Get detailed information about a specific monitor"""
    try:
        monitor = client.get_monitor(monitor_id)

        if not monitor:
            print(f"Monitor {monitor_id} not found.")
            sys.exit(1)

        print("Monitor Details")
        print("=" * 80)
        print()
        print(f"Name: {monitor.get('name', 'Unnamed')}")
        print(f"ID: {monitor.get('id')}")
        print(f"UID: {monitor.get('uid')}")
        print(f"Status: {'Active' if monitor.get('active', False) else 'Inactive'}")
        print()

        print("Configuration:")
        print(f"  Collection: {monitor.get('collection')}")
        if monitor.get('environment'):
            print(f"  Environment: {monitor.get('environment')}")

        if monitor.get('schedule'):
            schedule = monitor.get('schedule', {})
            print(f"  Schedule: {schedule.get('cron', 'Not configured')}")
            print(f"  Timezone: {schedule.get('timezone', 'UTC')}")

        print()

        if monitor.get('lastRun'):
            last_run = monitor.get('lastRun', {})
            print("Last Run:")
            print(f"  Status: {last_run.get('status', 'Unknown')}")
            print(f"  Started: {last_run.get('startedAt', 'N/A')}")
            print(f"  Finished: {last_run.get('finishedAt', 'N/A')}")

            stats = last_run.get('stats', {})
            if stats:
                print(f"  Assertions: {stats.get('assertions', {}).get('total', 0)} total, "
                      f"{stats.get('assertions', {}).get('failed', 0)} failed")

        print()

    except Exception as e:
        print(format_error("getting monitor details", e))
        sys.exit(1)


def create_monitor(client, name, collection_uid, environment_uid=None, schedule_cron=None):
    """Create a new monitor"""
    try:
        monitor_data = {
            'name': name,
            'collection': collection_uid
        }

        if environment_uid:
            monitor_data['environment'] = environment_uid

        if schedule_cron:
            monitor_data['schedule'] = {
                'cron': schedule_cron,
                'timezone': 'UTC'
            }

        print(f"Creating monitor '{name}'...")
        monitor = client.create_monitor(monitor_data)

        print("✓ Monitor created successfully!")
        print(f"  Name: {monitor.get('name')}")
        print(f"  ID: {monitor.get('id')}")
        print(f"  UID: {monitor.get('uid')}")
        print()

    except Exception as e:
        print(format_error("creating monitor", e))
        sys.exit(1)


def update_monitor(client, monitor_id, name=None, active=None, schedule_cron=None):
    """Update an existing monitor"""
    try:
        monitor_data = {}

        if name:
            monitor_data['name'] = name
        if active is not None:
            monitor_data['active'] = active
        if schedule_cron:
            monitor_data['schedule'] = {
                'cron': schedule_cron,
                'timezone': 'UTC'
            }

        if not monitor_data:
            print("No updates specified.")
            return

        print(f"Updating monitor {monitor_id}...")
        monitor = client.update_monitor(monitor_id, monitor_data)

        print("✓ Monitor updated successfully!")
        print(f"  Name: {monitor.get('name')}")
        print(f"  Status: {'Active' if monitor.get('active', False) else 'Inactive'}")
        print()

    except Exception as e:
        print(format_error("updating monitor", e))
        sys.exit(1)


def delete_monitor(client, monitor_id, confirm=False):
    """Delete a monitor"""
    try:
        if not confirm:
            print(f"Are you sure you want to delete monitor {monitor_id}?")
            print("Use --confirm to proceed.")
            sys.exit(1)

        print(f"Deleting monitor {monitor_id}...")
        client.delete_monitor(monitor_id)

        print("✓ Monitor deleted successfully!")
        print()

    except Exception as e:
        print(format_error("deleting monitor", e))
        sys.exit(1)


def analyze_monitor_runs(client, monitor_id, limit=10):
    """Analyze monitor run history"""
    try:
        runs = client.get_monitor_runs(monitor_id, limit=limit)

        if not runs:
            print(f"No run history found for monitor {monitor_id}.")
            return

        print(f"Monitor Run History (Last {len(runs)} runs)")
        print("=" * 80)
        print()

        total_runs = len(runs)
        successful_runs = sum(1 for run in runs if run.get('status') == 'success')
        failed_runs = total_runs - successful_runs

        print(f"Summary:")
        print(f"  Total Runs: {total_runs}")
        print(f"  Successful: {successful_runs} ({successful_runs/total_runs*100:.1f}%)")
        print(f"  Failed: {failed_runs} ({failed_runs/total_runs*100:.1f}%)")
        print()

        print("Recent Runs:")
        print("-" * 80)

        for i, run in enumerate(runs, 1):
            status = run.get('status', 'unknown')
            status_icon = "✓" if status == 'success' else "✗"

            started = run.get('startedAt', 'N/A')
            finished = run.get('finishedAt', 'N/A')

            # Calculate duration if both timestamps available
            duration = "N/A"
            if started != 'N/A' and finished != 'N/A':
                try:
                    start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
                    finish_dt = datetime.fromisoformat(finished.replace('Z', '+00:00'))
                    duration_seconds = (finish_dt - start_dt).total_seconds()
                    duration = f"{duration_seconds:.1f}s"
                except:
                    pass

            print(f"{i}. {status_icon} {status.upper()}")
            print(f"   Started: {started}")
            print(f"   Duration: {duration}")

            stats = run.get('stats', {})
            if stats:
                assertions = stats.get('assertions', {})
                requests = stats.get('requests', {})
                print(f"   Requests: {requests.get('total', 0)} total, {requests.get('failed', 0)} failed")
                print(f"   Assertions: {assertions.get('total', 0)} total, {assertions.get('failed', 0)} failed")

            print()

    except Exception as e:
        print(format_error("analyzing monitor runs", e))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Manage Postman Monitors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all monitors
  python manage_monitors.py --list

  # Get monitor details
  python manage_monitors.py --details <monitor-id>

  # Create a monitor
  python manage_monitors.py --create --name "API Health Check" --collection <collection-uid>

  # Update a monitor
  python manage_monitors.py --update <monitor-id> --name "New Name" --activate

  # Delete a monitor
  python manage_monitors.py --delete <monitor-id> --confirm

  # Analyze monitor runs
  python manage_monitors.py --analyze <monitor-id> --limit 20
        """
    )

    # Actions
    parser.add_argument('--list', action='store_true', help='List all monitors')
    parser.add_argument('--details', metavar='ID', help='Get monitor details')
    parser.add_argument('--create', action='store_true', help='Create a new monitor')
    parser.add_argument('--update', metavar='ID', help='Update a monitor')
    parser.add_argument('--delete', metavar='ID', help='Delete a monitor')
    parser.add_argument('--analyze', metavar='ID', help='Analyze monitor run history')

    # Options
    parser.add_argument('--name', help='Monitor name')
    parser.add_argument('--collection', help='Collection UID')
    parser.add_argument('--environment', help='Environment UID')
    parser.add_argument('--schedule', help='Cron schedule (e.g., "0 */6 * * *" for every 6 hours)')
    parser.add_argument('--activate', action='store_true', help='Activate the monitor')
    parser.add_argument('--deactivate', action='store_true', help='Deactivate the monitor')
    parser.add_argument('--confirm', action='store_true', help='Confirm deletion')
    parser.add_argument('--limit', type=int, default=10, help='Number of runs to analyze (default: 10)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    # Validate arguments
    if not any([args.list, args.details, args.create, args.update, args.delete, args.analyze]):
        parser.print_help()
        sys.exit(1)

    # Get configuration and create client
    config = get_config()
    client = PostmanClient(config)

    # Execute action
    if args.list:
        list_monitors(client, verbose=args.verbose)

    elif args.details:
        get_monitor_details(client, args.details)

    elif args.create:
        if not args.name or not args.collection:
            print("Error: --name and --collection are required for creating a monitor")
            sys.exit(1)
        create_monitor(client, args.name, args.collection, args.environment, args.schedule)

    elif args.update:
        active = None
        if args.activate:
            active = True
        elif args.deactivate:
            active = False
        update_monitor(client, args.update, args.name, active, args.schedule)

    elif args.delete:
        delete_monitor(client, args.delete, args.confirm)

    elif args.analyze:
        analyze_monitor_runs(client, args.analyze, args.limit)


if __name__ == '__main__':
    main()
