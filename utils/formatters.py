"""
Output formatters for Postman API responses.
Makes API data human-readable for Claude and users.
"""

from datetime import datetime


def format_collections_list(collections):
    """
    Format a list of collections into readable output.

    Args:
        collections: List of collection objects from Postman API

    Returns:
        Formatted string representation
    """
    if not collections:
        return "No collections found in this workspace."

    output = []
    output.append(f"Found {len(collections)} collection(s):")
    output.append("")

    for idx, collection in enumerate(collections, 1):
        name = collection.get('name', 'Unnamed Collection')
        uid = collection.get('uid', 'N/A')
        output.append(f"{idx}. {name}")
        output.append(f"   UID: {uid}")
        if 'owner' in collection:
            output.append(f"   Owner: {collection['owner']}")
        output.append("")

    return "\n".join(output)


def format_environments_list(environments):
    """
    Format a list of environments into readable output.

    Args:
        environments: List of environment objects from Postman API

    Returns:
        Formatted string representation
    """
    if not environments:
        return "No environments found in this workspace."

    output = []
    output.append(f"Found {len(environments)} environment(s):")
    output.append("")

    for idx, env in enumerate(environments, 1):
        name = env.get('name', 'Unnamed Environment')
        uid = env.get('uid', 'N/A')
        output.append(f"{idx}. {name}")
        output.append(f"   UID: {uid}")
        output.append("")

    return "\n".join(output)


def format_monitors_list(monitors):
    """
    Format a list of monitors into readable output.

    Args:
        monitors: List of monitor objects from Postman API

    Returns:
        Formatted string representation
    """
    if not monitors:
        return "No monitors found in this workspace."

    output = []
    output.append(f"Found {len(monitors)} monitor(s):")
    output.append("")

    for idx, monitor in enumerate(monitors, 1):
        name = monitor.get('name', 'Unnamed Monitor')
        uid = monitor.get('uid', 'N/A')
        output.append(f"{idx}. {name}")
        output.append(f"   UID: {uid}")
        if 'collection' in monitor:
            output.append(f"   Collection: {monitor['collection']}")
        output.append("")

    return "\n".join(output)


def format_apis_list(apis):
    """
    Format a list of APIs into readable output.

    Args:
        apis: List of API objects from Postman API

    Returns:
        Formatted string representation
    """
    if not apis:
        return "No APIs found in this workspace."

    output = []
    output.append(f"Found {len(apis)} API(s):")
    output.append("")

    for idx, api in enumerate(apis, 1):
        name = api.get('name', 'Unnamed API')
        api_id = api.get('id', 'N/A')
        output.append(f"{idx}. {name}")
        output.append(f"   ID: {api_id}")
        if 'summary' in api:
            output.append(f"   Summary: {api['summary']}")
        output.append("")

    return "\n".join(output)


def format_workspace_summary(collections, environments, monitors, apis):
    """
    Format a complete workspace summary.

    Args:
        collections: List of collections
        environments: List of environments
        monitors: List of monitors
        apis: List of APIs

    Returns:
        Formatted string representation
    """
    output = []
    output.append("=== Workspace Summary ===")
    output.append("")
    output.append(f"Collections: {len(collections)}")
    output.append(f"Environments: {len(environments)}")
    output.append(f"Monitors: {len(monitors)}")
    output.append(f"APIs: {len(apis)}")
    output.append("")
    output.append("Use specific list commands to see details:")
    output.append("- List collections: python /skills/postman-skill/scripts/list_collections.py")
    output.append("- List environments: python /skills/postman-skill/scripts/list_collections.py --environments")
    output.append("- List monitors: python /skills/postman-skill/scripts/list_collections.py --monitors")
    output.append("- List APIs: python /skills/postman-skill/scripts/list_collections.py --apis")
    output.append("")

    return "\n".join(output)


def format_error(error, context=""):
    """
    Format an error message with helpful guidance.

    Args:
        error: Exception or error message
        context: Additional context about what was being attempted

    Returns:
        Formatted error message
    """
    output = []
    output.append("=== Error ===")
    if context:
        output.append(f"Context: {context}")
    output.append(f"Error: {str(error)}")
    output.append("")
    output.append("Troubleshooting steps:")
    output.append("1. Check that POSTMAN_API_KEY is set correctly")
    output.append("2. Verify your API key has the necessary permissions")
    output.append("3. Check if the resource ID/UID is correct")
    output.append("4. Review the Postman API status: https://status.postman.com/")
    output.append("")

    return "\n".join(output)


def format_monitor(monitor, verbose=False):
    """
    Format a single monitor for display.

    Args:
        monitor: Monitor object from API
        verbose: Include detailed information

    Returns:
        Formatted string representation
    """
    output = []

    # Status and name
    status = "✓ Active" if monitor.get('active', False) else "✗ Inactive"
    name = monitor.get('name', 'Unnamed Monitor')
    output.append(f"{status} {name}")
    output.append(f"   ID: {monitor.get('id')}")
    output.append(f"   UID: {monitor.get('uid')}")

    if verbose:
        if monitor.get('collectionUid'):
            output.append(f"   Collection: {monitor.get('collectionUid')}")
        if monitor.get('environmentUid'):
            output.append(f"   Environment: {monitor.get('environmentUid')}")
        if monitor.get('schedule'):
            schedule = monitor.get('schedule', {})
            output.append(f"   Schedule: {schedule.get('cron', 'Not set')}")
        if monitor.get('lastRun'):
            last_run = monitor.get('lastRun', {})
            output.append(f"   Last Run: {last_run.get('finishedAt', 'Never')}")
            if last_run.get('status'):
                output.append(f"   Last Status: {last_run.get('status')}")

    return "\n".join(output)


def format_monitor_run(run, index=None):
    """
    Format a monitor run for display.

    Args:
        run: Monitor run object from API
        index: Optional index number for the run

    Returns:
        Formatted string representation
    """
    from datetime import datetime

    output = []

    status = run.get('status', 'unknown')
    status_icon = "✓" if status == 'success' else "✗"

    # Run number
    if index is not None:
        output.append(f"{index}. {status_icon} {status.upper()}")
    else:
        output.append(f"{status_icon} {status.upper()}")

    # Timestamps
    started = run.get('startedAt', 'N/A')
    finished = run.get('finishedAt', 'N/A')
    output.append(f"   Started: {started}")

    # Calculate duration
    duration = "N/A"
    if started != 'N/A' and finished != 'N/A':
        try:
            start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
            finish_dt = datetime.fromisoformat(finished.replace('Z', '+00:00'))
            duration_seconds = (finish_dt - start_dt).total_seconds()
            duration = f"{duration_seconds:.1f}s"
        except:
            pass

    output.append(f"   Duration: {duration}")

    # Stats
    stats = run.get('stats', {})
    if stats:
        requests = stats.get('requests', {})
        assertions = stats.get('assertions', {})
        output.append(f"   Requests: {requests.get('total', 0)} total, {requests.get('failed', 0)} failed")
        output.append(f"   Assertions: {assertions.get('total', 0)} total, {assertions.get('failed', 0)} failed")

    return "\n".join(output)


def format_monitor_runs_summary(runs):
    """
    Format a summary of monitor runs.

    Args:
        runs: List of monitor run objects

    Returns:
        Formatted string representation
    """
    if not runs:
        return "No run history available."

    output = []

    # Calculate statistics
    total_runs = len(runs)
    successful_runs = sum(1 for run in runs if run.get('status') == 'success')
    failed_runs = total_runs - successful_runs

    output.append(f"Monitor Run History (Last {total_runs} runs)")
    output.append("=" * 80)
    output.append("")

    # Summary
    output.append("Summary:")
    output.append(f"  Total Runs: {total_runs}")
    output.append(f"  Successful: {successful_runs} ({successful_runs/total_runs*100:.1f}%)")
    output.append(f"  Failed: {failed_runs} ({failed_runs/total_runs*100:.1f}%)")
    output.append("")

    # Recent runs
    output.append("Recent Runs:")
    output.append("-" * 80)

    for i, run in enumerate(runs, 1):
        output.append(format_monitor_run(run, i))
        output.append("")

    return "\n".join(output)
