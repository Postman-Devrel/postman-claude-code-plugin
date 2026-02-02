"""
Postman API client with retry logic and error handling.
"""

import sys
import os
import warnings
import subprocess
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.config import PostmanConfig
from utils.retry_handler import RetryHandler
from utils.exceptions import (
    create_exception_from_response,
    NetworkError,
    TimeoutError
)


class PostmanClient:
    """
    Client for interacting with the Postman API.
    Handles authentication, retries, and response parsing.

    Supports Postman v10+ APIs with backward compatibility detection.
    """

    def __init__(self, config=None):
        self.config = config or PostmanConfig()
        self.config.validate()
        self.retry_handler = RetryHandler(max_retries=self.config.max_retries)
        self.api_version = None  # Will be detected on first request
        self.api_version_warned = False  # Track if we've warned about old version

    def _detect_api_version(self, response):
        """
        Detect API version from response.

        This is primarily for logging and user awareness.
        Args:
            response: requests.Response object
        """
        # Try X-API-Version header first
        version_header = response.headers.get('X-API-Version')
        if version_header:
            self.api_version = version_header
            return

        # Try to infer from response structure
        try:
            data = response.json()
            # v10+ typically includes 'meta' fields
            if self._has_v10_structure(data):
                self.api_version = 'v10+'
            else:
                self.api_version = 'v9-or-earlier'
        except:
            self.api_version = 'unknown'

        # Warn if using old version
        if self.api_version and not str(self.api_version).startswith('v10') and not self.api_version_warned:
            self._warn_about_old_version()

    def _has_v10_structure(self, data):
        """
        Check if response has v10+ structure indicators.

        Args:
            data: Parsed JSON response

        Returns:
            True if response appears to be v10+, False otherwise
        """
        # Check for v10+ metadata indicators
        if 'meta' in data:
            return True

        # Check collection/environment structure
        if 'collection' in data:
            collection = data['collection']
            if 'fork' in collection or 'meta' in collection:
                return True

        # Default to assuming v10+ (optimistic)
        return True

    def _warn_about_old_version(self):
        """Warn user about using older API version."""
        if not self.api_version_warned:
            warnings.warn(
                f"Detected API version: {self.api_version}. "
                "This skill is optimized for Postman v10+ APIs. "
                "Some features may not work correctly with older versions. "
                "Please upgrade to Postman v10+ for best experience.",
                UserWarning
            )
            self.api_version_warned = True

    def _make_request(self, method, endpoint, **kwargs):
        """
        Make an API request with retry logic and enhanced error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            endpoint: API endpoint path (without base URL)
            **kwargs: Additional arguments (json, headers, etc.)

        Returns:
            Parsed JSON response

        Raises:
            AuthenticationError: If authentication fails (401)
            PermissionError: If insufficient permissions (403)
            ResourceNotFoundError: If resource not found (404)
            ValidationError: If request validation fails (400)
            RateLimitError: If rate limit exceeded (429)
            ServerError: If server error occurs (5xx)
            NetworkError: If network connection fails
            TimeoutError: If request times out
            PostmanAPIError: For other API errors
        """
        url = f"{self.config.base_url}{endpoint}"

        # Build curl command
        curl_cmd = ['curl', '-s', '-k', '-i']  # silent, skip cert verification, include headers

        # Add HTTP method for non-GET requests
        if method.upper() != 'GET':
            curl_cmd.extend(['-X', method.upper()])

        # Add JSON body if provided (before headers to avoid duplicates)
        has_json_body = 'json' in kwargs and kwargs['json']
        if has_json_body:
            json_data = json.dumps(kwargs['json'])
            curl_cmd.extend(['-d', json_data])
            curl_cmd.extend(['-H', 'Content-Type: application/json'])

        # Add headers (skip Content-Type if we already added it for JSON)
        for key, value in self.config.headers.items():
            if key.lower() == 'content-type' and has_json_body:
                continue  # Skip duplicate Content-Type
            curl_cmd.extend(['-H', f"{key}: {value}"])

        # Add timeout
        timeout = kwargs.get('timeout', self.config.timeout)
        curl_cmd.extend(['--max-time', str(timeout)])

        # Add URL
        curl_cmd.append(url)

        def execute_curl():
            """Execute curl command and return parsed response."""
            try:
                # Use environment as-is - the proxy is configured correctly
                # and removing it breaks DNS resolution
                env = os.environ.copy()

                # Debug: print curl command if POSTMAN_DEBUG is set
                if os.getenv('POSTMAN_DEBUG'):
                    print(f"DEBUG: Executing curl command: {' '.join(curl_cmd[:10])}... {url}", file=sys.stderr)
                    print(f"DEBUG: Using proxy: {env.get('https_proxy', 'none')}", file=sys.stderr)

                result = subprocess.run(
                    curl_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout + 5,  # Add buffer to subprocess timeout
                    env=env  # Use environment with proxy intact
                )

                if result.returncode != 0:
                    stderr = result.stderr.strip() if result.stderr else ""
                    stdout = result.stdout.strip() if result.stdout else ""
                    error_msg = stderr or stdout or "Unknown curl error"
                    raise NetworkError(
                        message=f"Curl failed (exit code {result.returncode}): {error_msg}\n"
                                f"Command: {' '.join(curl_cmd[:4])}... {url}"
                    )

                # Parse response (headers + body)
                output = result.stdout
                if not output:
                    raise NetworkError(message="Empty response from curl")

                # Split headers and body
                parts = output.split('\r\n\r\n', 1)
                if len(parts) < 2:
                    parts = output.split('\n\n', 1)

                if len(parts) < 2:
                    raise NetworkError(message="Invalid response format from curl")

                headers_text, body = parts[0], parts[1]

                # Check if body contains another HTTP response (common with proxies/HTTP2)
                if body.strip().startswith('HTTP/'):
                    # The body is actually another HTTP response - parse it instead
                    nested_parts = body.split('\n\n', 1)
                    if len(nested_parts) >= 2:
                        headers_text = nested_parts[0]
                        body = nested_parts[1] if len(nested_parts) > 1 else ""

                # Debug: print response details if POSTMAN_DEBUG is set
                if os.getenv('POSTMAN_DEBUG'):
                    print(f"DEBUG: Headers (first 200 chars): {headers_text[:200]}", file=sys.stderr)
                    print(f"DEBUG: Response body length: {len(body)}", file=sys.stderr)
                    print(f"DEBUG: Response body (first 200 chars): {body[:200]}", file=sys.stderr)

                # Extract status code from headers
                status_line = headers_text.split('\n')[0]
                status_parts = status_line.split()
                if len(status_parts) < 2:
                    raise NetworkError(message=f"Invalid HTTP status line: {status_line}")
                status_code = int(status_parts[1])

                # Parse response headers
                response_headers = {}
                for line in headers_text.split('\n')[1:]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        response_headers[key.strip()] = value.strip()

                # Create a mock response object for compatibility
                class MockResponse:
                    def __init__(self, status_code, headers, body):
                        self.status_code = status_code
                        self.headers = headers
                        self._body = body

                    def json(self):
                        return json.loads(self._body) if self._body else {}

                return MockResponse(status_code, response_headers, body)

            except subprocess.TimeoutExpired as e:
                raise TimeoutError(timeout_seconds=timeout) from e
            except json.JSONDecodeError as e:
                # Better error for empty/invalid responses
                error_msg = (
                    "Received invalid JSON response from Postman API.\n"
                    "This usually means:\n"
                    "  • The endpoint returned no data or empty response\n"
                    "  • Network connectivity issue\n"
                    "  • The API endpoint might not exist\n"
                    f"\nTried to access: {url}\n"
                    "\n🔧 Troubleshooting:\n"
                    "  • Run: python scripts/validate_setup.py\n"
                    "  • Check Postman API status: https://status.postman.com/"
                )
                raise NetworkError(message=error_msg) from e
            except Exception as e:
                if isinstance(e, (NetworkError, TimeoutError)):
                    raise
                raise NetworkError(message=f"Request failed: {str(e)}", original_error=e) from e

        try:
            # Use retry handler
            response = self.retry_handler.execute(execute_curl)
        except TimeoutError:
            raise
        except NetworkError:
            raise
        except Exception as e:
            raise NetworkError(
                message=f"Request failed: {str(e)}",
                original_error=e
            ) from e

        # Detect API version on first request
        if self.api_version is None:
            self._detect_api_version(response)

        # Handle error responses
        if response.status_code >= 400:
            raise create_exception_from_response(response)

        # Return parsed response
        return response.json()

    def list_collections(self, workspace_id=None):
        """
        List all collections in a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            List of collection objects
        """
        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/collections?workspace={workspace_id}"
        else:
            endpoint = "/collections"

        response = self._make_request('GET', endpoint)
        collections = response.get('collections', [])

        # Provide helpful context for empty results (only in debug mode)
        if len(collections) == 0 and os.getenv('POSTMAN_DEBUG'):
            if workspace_id:
                import sys
                print(f"ℹ️  No collections found in workspace {workspace_id}", file=sys.stderr)
                print("   💡 Run 'python scripts/list_workspaces.py' to see other workspaces", file=sys.stderr)

        return collections

    def get_collection(self, collection_uid):
        """
        Get detailed information about a specific collection.

        Args:
            collection_uid: Unique identifier for the collection

        Returns:
            Collection object with full details
        """
        endpoint = f"/collections/{collection_uid}"
        response = self._make_request('GET', endpoint)
        return response.get('collection', {})

    def create_collection(self, collection_data, workspace_id=None):
        """
        Create a new collection.

        Args:
            collection_data: Dictionary containing collection configuration:
                - info: Collection metadata (name, description, schema)
                - item: List of requests/folders (optional)
                - variable: List of collection variables (optional)
            workspace_id: Workspace ID to create collection in (uses config default if not provided)

        Returns:
            Created collection object
        """
        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/collections?workspace={workspace_id}"
        else:
            endpoint = "/collections"

        response = self._make_request('POST', endpoint, json={'collection': collection_data})
        return response.get('collection', {})

    def update_collection(self, collection_uid, collection_data):
        """
        Update an existing collection.

        Args:
            collection_uid: Unique identifier for the collection
            collection_data: Dictionary containing fields to update

        Returns:
            Updated collection object
        """
        endpoint = f"/collections/{collection_uid}"
        response = self._make_request('PUT', endpoint, json={'collection': collection_data})
        return response.get('collection', {})

    def delete_collection(self, collection_uid):
        """
        Delete a collection.

        Args:
            collection_uid: Unique identifier for the collection

        Returns:
            Deletion confirmation
        """
        endpoint = f"/collections/{collection_uid}"
        response = self._make_request('DELETE', endpoint)
        return response

    def fork_collection(self, collection_uid, label=None, workspace_id=None):
        """
        Create a fork of a collection.

        **Requires**: Postman v10+ API

        A fork is an independent copy of a collection that can be modified
        separately. Forks enable version control workflows with pull requests.

        Args:
            collection_uid: Collection UID to fork
            label: Optional label/name for the fork
            workspace_id: Workspace for the fork (uses config default if not provided)

        Returns:
            Forked collection object with fork metadata

        Example:
            >>> client.fork_collection(
            ...     collection_uid="12345-abcd",
            ...     label="my-feature-branch",
            ...     workspace_id="67890-efgh"
            ... )
        """
        workspace_id = workspace_id or self.config.workspace_id

        endpoint = f"/collections/{collection_uid}/forks"
        payload = {}

        if label:
            payload['label'] = label
        if workspace_id:
            payload['workspace'] = workspace_id

        response = self._make_request('POST', endpoint, json=payload)
        return response.get('fork', {})

    def create_pull_request(self, collection_uid, source_collection_uid,
                           title=None, description=None, reviewers=None):
        """
        Create a pull request to merge changes from a forked collection.

        **Requires**: Postman v10+ API

        Pull requests allow you to propose merging changes from a fork
        back to the parent collection.

        Args:
            collection_uid: Destination collection UID (parent)
            source_collection_uid: Source collection UID (fork)
            title: Pull request title
            description: Pull request description
            reviewers: List of reviewer user IDs (optional)

        Returns:
            Pull request object

        Example:
            >>> client.create_pull_request(
            ...     collection_uid="parent-12345",
            ...     source_collection_uid="fork-67890",
            ...     title="Add new authentication tests",
            ...     description="This PR adds comprehensive auth tests"
            ... )
        """
        endpoint = f"/collections/{collection_uid}/pull-requests"
        payload = {
            'source': source_collection_uid
        }

        if title:
            payload['title'] = title
        if description:
            payload['description'] = description
        if reviewers:
            payload['reviewers'] = reviewers

        response = self._make_request('POST', endpoint, json=payload)
        return response.get('pull_request', {})

    def get_pull_requests(self, collection_uid, status=None):
        """
        Get pull requests for a collection.

        **Requires**: Postman v10+ API

        Args:
            collection_uid: Collection UID
            status: Filter by status ('open', 'closed', 'merged') (optional)

        Returns:
            List of pull request objects

        Example:
            >>> # Get all open PRs
            >>> client.get_pull_requests("12345-abcd", status="open")
        """
        endpoint = f"/collections/{collection_uid}/pull-requests"

        if status:
            endpoint += f"?status={status}"

        response = self._make_request('GET', endpoint)
        return response.get('pull_requests', [])

    def merge_pull_request(self, collection_uid, pull_request_id):
        """
        Merge a pull request.

        **Requires**: Postman v10+ API

        Merges the changes from a fork into the parent collection.

        Args:
            collection_uid: Collection UID
            pull_request_id: Pull request ID to merge

        Returns:
            Merged pull request object

        Example:
            >>> client.merge_pull_request("12345-abcd", "pr-789")
        """
        endpoint = f"/collections/{collection_uid}/pull-requests/{pull_request_id}/merge"
        response = self._make_request('POST', endpoint)
        return response.get('pull_request', {})

    def duplicate_collection(self, collection_uid, name=None, workspace_id=None):
        """
        Duplicate a collection (create a copy, not a fork).

        Creates a complete copy of a collection without version control linkage.
        Unlike forking, duplicating creates a standalone collection.

        Args:
            collection_uid: Collection UID to duplicate
            name: Name for the duplicate (defaults to original name + " Copy")
            workspace_id: Workspace for duplicate (uses config default if not provided)

        Returns:
            Duplicated collection object

        Example:
            >>> client.duplicate_collection(
            ...     collection_uid="12345-abcd",
            ...     name="My Collection Backup"
            ... )
        """
        # Get original collection
        original = self.get_collection(collection_uid)

        # Prepare new collection data
        new_collection = original.copy()

        # Set new name
        if name:
            new_collection['info']['name'] = name
        else:
            original_name = original.get('info', {}).get('name', 'Collection')
            new_collection['info']['name'] = f"{original_name} Copy"

        # Remove UID and other metadata that shouldn't be copied
        if 'uid' in new_collection.get('info', {}):
            del new_collection['info']['uid']
        if '_postman_id' in new_collection.get('info', {}):
            del new_collection['info']['_postman_id']

        # Create new collection
        return self.create_collection(new_collection, workspace_id)

    def list_environments(self, workspace_id=None):
        """
        List all environments in a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            List of environment objects
        """
        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/environments?workspace={workspace_id}"
        else:
            endpoint = "/environments"

        response = self._make_request('GET', endpoint)
        return response.get('environments', [])

    def get_environment(self, environment_uid):
        """
        Get detailed information about a specific environment.

        Args:
            environment_uid: Unique identifier for the environment

        Returns:
            Environment object with full details
        """
        endpoint = f"/environments/{environment_uid}"
        response = self._make_request('GET', endpoint)
        return response.get('environment', {})

    def create_environment(self, name, values=None, workspace_id=None):
        """
        Create a new environment with automatic secret detection.

        **Enhanced in v2.0**: Automatically detects sensitive variables and
        marks them as secrets.

        Args:
            name: Environment name
            values: Dict of variable name -> value pairs, or list of variable objects
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            Created environment object

        Example:
            >>> # Simple dict format with auto-secret detection
            >>> client.create_environment(
            ...     name="Production",
            ...     values={
            ...         "base_url": "https://api.example.com",
            ...         "api_key": "secret-key-123",  # Auto-detected as secret
            ...         "timeout": "30"
            ...     }
            ... )
            >>>
            >>> # Advanced format with explicit types
            >>> client.create_environment(
            ...     name="Production",
            ...     values=[
            ...         {"key": "base_url", "value": "https://api.example.com", "type": "default"},
            ...         {"key": "api_key", "value": "secret-key-123", "type": "secret"}
            ...     ]
            ... )
        """
        workspace_id = workspace_id or self.config.workspace_id

        endpoint = "/environments"
        if workspace_id:
            endpoint += f"?workspace={workspace_id}"

        # Format variables
        variables = []
        if values:
            if isinstance(values, dict):
                # Convert dict to variable list with auto-secret detection
                for key, value in values.items():
                    var = {
                        'key': key,
                        'value': str(value),
                        'type': self._detect_secret_type(key),
                        'enabled': True
                    }
                    variables.append(var)
            elif isinstance(values, list):
                # Use provided list, ensure all have required fields
                for var in values:
                    if 'type' not in var:
                        var['type'] = self._detect_secret_type(var.get('key', ''))
                    if 'enabled' not in var:
                        var['enabled'] = True
                    variables.append(var)

        payload = {
            'environment': {
                'name': name,
                'values': variables
            }
        }

        response = self._make_request('POST', endpoint, json=payload)
        return response.get('environment', {})

    def _detect_secret_type(self, key):
        """
        Detect if a variable should be marked as secret based on its name.

        Args:
            key: Variable name

        Returns:
            'secret' if the variable appears sensitive, 'default' otherwise
        """
        sensitive_keywords = [
            'key', 'token', 'secret', 'password', 'passwd',
            'pwd', 'auth', 'credential', 'private', 'apikey',
            'api_key', 'bearer', 'authorization'
        ]

        key_lower = key.lower()
        for keyword in sensitive_keywords:
            if keyword in key_lower:
                return 'secret'

        return 'default'

    def update_environment(self, environment_uid, name=None, values=None):
        """
        Update an existing environment.

        **Enhanced in v2.0**: Supports partial updates and automatic secret detection.

        Args:
            environment_uid: Environment UID
            name: New name (optional)
            values: Dict of variable updates or list of variables (optional)

        Returns:
            Updated environment object

        Example:
            >>> # Update just the name
            >>> client.update_environment("env-123", name="Staging v2")
            >>>
            >>> # Update/add variables
            >>> client.update_environment(
            ...     "env-123",
            ...     values={
            ...         "api_key": "new-secret-key",  # Updates existing or adds new
            ...         "new_var": "value"
            ...     }
            ... )
        """
        endpoint = f"/environments/{environment_uid}"

        # Get current environment
        current = self.get_environment(environment_uid)

        # Update name if provided
        if name:
            current['name'] = name

        # Update variables if provided
        if values:
            current_vars = {v['key']: v for v in current.get('values', [])}

            if isinstance(values, dict):
                # Update existing or add new variables
                for key, value in values.items():
                    if key in current_vars:
                        # Update existing variable
                        current_vars[key]['value'] = str(value)
                        # Preserve type unless it should be secret
                        if current_vars[key].get('type') != 'secret':
                            current_vars[key]['type'] = self._detect_secret_type(key)
                    else:
                        # Add new variable
                        var = {
                            'key': key,
                            'value': str(value),
                            'type': self._detect_secret_type(key),
                            'enabled': True
                        }
                        current_vars[key] = var

                current['values'] = list(current_vars.values())

            elif isinstance(values, list):
                # Replace all variables
                for var in values:
                    if 'type' not in var:
                        var['type'] = self._detect_secret_type(var.get('key', ''))
                    if 'enabled' not in var:
                        var['enabled'] = True
                current['values'] = values

        payload = {'environment': current}
        response = self._make_request('PUT', endpoint, json=payload)
        return response.get('environment', {})

    def delete_environment(self, environment_uid):
        """
        Delete an environment.

        Args:
            environment_uid: Unique identifier for the environment

        Returns:
            Deletion confirmation
        """
        endpoint = f"/environments/{environment_uid}"
        response = self._make_request('DELETE', endpoint)
        return response

    def duplicate_environment(self, environment_uid, name=None, workspace_id=None):
        """
        Duplicate an environment.

        Creates a complete copy of an environment including all variables.
        Secret variables are preserved with their secret type.

        Args:
            environment_uid: Environment UID to duplicate
            name: Name for the duplicate (defaults to original name + " Copy")
            workspace_id: Workspace for duplicate (uses config default if not provided)

        Returns:
            Duplicated environment object

        Example:
            >>> client.duplicate_environment(
            ...     environment_uid="env-123",
            ...     name="Production Backup"
            ... )
        """
        # Get original environment
        original = self.get_environment(environment_uid)

        # Prepare new environment name
        new_name = name or f"{original['name']} Copy"

        # Extract variables (preserve types including secrets)
        values = original.get('values', [])

        # Create new environment
        return self.create_environment(new_name, values, workspace_id)

    def run_collection(self, collection_uid, environment_uid=None):
        """
        Run a collection's tests.

        Note: This requires additional Postman features like Newman or Collection Runner.
        For the POC, this is a placeholder showing the intended structure.

        Args:
            collection_uid: Unique identifier for the collection
            environment_uid: Optional environment to use

        Returns:
            Test run results
        """
        # Note: The actual test running would typically use Newman or the Collection Runner API
        # This is a simplified version for the POC
        raise NotImplementedError(
            "Collection test execution requires Postman Collection Runner or Newman integration. "
            "This POC demonstrates the API client structure. "
            "For now, use 'list_collections' to discover available collections."
        )

    def list_monitors(self, workspace_id=None):
        """
        List all monitors in a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            List of monitor objects
        """
        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/monitors?workspace={workspace_id}"
        else:
            endpoint = "/monitors"

        response = self._make_request('GET', endpoint)
        return response.get('monitors', [])

    def get_monitor(self, monitor_id):
        """
        Get detailed information about a specific monitor.

        Args:
            monitor_id: Unique identifier for the monitor

        Returns:
            Monitor object with full details
        """
        endpoint = f"/monitors/{monitor_id}"
        response = self._make_request('GET', endpoint)
        return response.get('monitor', {})

    def create_monitor(self, monitor_data):
        """
        Create a new monitor.

        Args:
            monitor_data: Dictionary containing monitor configuration:
                - name: Monitor name
                - collection: Collection UID
                - environment: Environment UID (optional)
                - schedule: Schedule configuration (optional)

        Returns:
            Created monitor object
        """
        endpoint = "/monitors"
        response = self._make_request('POST', endpoint, json={'monitor': monitor_data})
        return response.get('monitor', {})

    def update_monitor(self, monitor_id, monitor_data):
        """
        Update an existing monitor.

        Args:
            monitor_id: Unique identifier for the monitor
            monitor_data: Dictionary containing fields to update

        Returns:
            Updated monitor object
        """
        endpoint = f"/monitors/{monitor_id}"
        response = self._make_request('PUT', endpoint, json={'monitor': monitor_data})
        return response.get('monitor', {})

    def delete_monitor(self, monitor_id):
        """
        Delete a monitor.

        Args:
            monitor_id: Unique identifier for the monitor

        Returns:
            Deletion confirmation
        """
        endpoint = f"/monitors/{monitor_id}"
        response = self._make_request('DELETE', endpoint)
        return response

    def get_monitor_runs(self, monitor_id, limit=10):
        """
        Get run history for a monitor.

        Args:
            monitor_id: Unique identifier for the monitor
            limit: Number of runs to retrieve (default: 10)

        Returns:
            List of monitor run objects
        """
        endpoint = f"/monitors/{monitor_id}/runs?limit={limit}"
        response = self._make_request('GET', endpoint)
        return response.get('runs', [])

    def list_apis(self, workspace_id=None):
        """
        List all APIs in a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            List of API objects
        """
        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/apis?workspace={workspace_id}"
        else:
            endpoint = "/apis"

        response = self._make_request('GET', endpoint)
        return response.get('apis', [])

    def get_workspace(self, workspace_id=None):
        """
        Get information about a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            Workspace object with details
        """
        workspace_id = workspace_id or self.config.workspace_id

        if not workspace_id:
            raise ValueError("Workspace ID must be provided or set in configuration")

        endpoint = f"/workspaces/{workspace_id}"
        response = self._make_request('GET', endpoint)
        return response.get('workspace', {})

    # Design Phase: Schema and API Operations

    def get_api(self, api_id):
        """
        Get detailed information about a specific API.

        Args:
            api_id: Unique identifier for the API

        Returns:
            API object with full details
        """
        endpoint = f"/apis/{api_id}"
        response = self._make_request('GET', endpoint)
        return response.get('api', {})

    def get_api_versions(self, api_id):
        """
        Get all versions of an API.

        Args:
            api_id: Unique identifier for the API

        Returns:
            List of API version objects
        """
        endpoint = f"/apis/{api_id}/versions"
        response = self._make_request('GET', endpoint)
        return response.get('versions', [])

    def get_api_version(self, api_id, version_id):
        """
        Get a specific version of an API.

        Args:
            api_id: Unique identifier for the API
            version_id: Unique identifier for the version

        Returns:
            API version object with details
        """
        endpoint = f"/apis/{api_id}/versions/{version_id}"
        response = self._make_request('GET', endpoint)
        return response.get('version', {})

    def get_api_schema(self, api_id, version_id):
        """
        Get the schema for a specific API version.

        Args:
            api_id: Unique identifier for the API
            version_id: Unique identifier for the version

        Returns:
            Schema object
        """
        endpoint = f"/apis/{api_id}/versions/{version_id}/schemas"
        response = self._make_request('GET', endpoint)
        return response.get('schemas', [])

    def create_api(self, api_data, workspace_id=None):
        """
        Create a new API.

        **DEPRECATED**: This method uses the legacy API creation approach.
        Please use create_spec() instead, which creates specifications in Postman's Spec Hub.

        The Spec Hub is the recommended way to manage API specifications as it provides:
        - Direct specification management (OpenAPI 3.0, AsyncAPI 2.0)
        - Multi-file specification support
        - Bidirectional collection generation
        - Better version control integration

        See: create_spec() for the new approach

        Args:
            api_data: Dictionary containing API configuration:
                - name: API name
                - summary: API summary (optional)
                - description: API description (optional)
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            Created API object
        """
        # Warn users about deprecation
        warnings.warn(
            "create_api() is deprecated and will be removed in a future version. "
            "Please use create_spec() to create specifications in Postman's Spec Hub instead. "
            "See: https://learning.postman.com/docs/design-apis/specifications/overview/",
            DeprecationWarning,
            stacklevel=2
        )

        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/apis?workspace={workspace_id}"
        else:
            endpoint = "/apis"

        response = self._make_request('POST', endpoint, json={'api': api_data})
        return response.get('api', {})

    def update_api(self, api_id, api_data):
        """
        Update an existing API.

        Args:
            api_id: Unique identifier for the API
            api_data: Dictionary containing fields to update

        Returns:
            Updated API object
        """
        endpoint = f"/apis/{api_id}"
        response = self._make_request('PUT', endpoint, json={'api': api_data})
        return response.get('api', {})

    def delete_api(self, api_id):
        """
        Delete an API.

        Args:
            api_id: Unique identifier for the API

        Returns:
            Deletion confirmation
        """
        endpoint = f"/apis/{api_id}"
        response = self._make_request('DELETE', endpoint)
        return response

    # Spec Hub Operations (Replaces legacy API creation)

    def create_spec(self, spec_data, workspace_id=None):
        """
        Create a new API specification in Postman's Spec Hub.

        **This is the recommended way to create API specifications.**
        The legacy create_api() method is deprecated in favor of Spec Hub.

        Supports both single-file and multi-file specifications.
        For OpenAPI 3.0 and AsyncAPI 2.0.

        Args:
            spec_data: Dictionary containing specification configuration:
                - name: Spec name (required)
                - description: Spec description (optional)
                - files: List of file objects (required):
                    - path: File path (e.g., "openapi.yaml")
                    - content: File content as string (JSON or YAML)
                    - root: Boolean, mark as root file (optional, default: first file)
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            Created spec object with spec ID and metadata

        Example:
            >>> # Single-file OpenAPI 3.0 spec
            >>> client.create_spec({
            ...     "name": "Pet Store API",
            ...     "description": "A simple pet store API",
            ...     "files": [{
            ...         "path": "openapi.yaml",
            ...         "content": yaml_or_json_string,
            ...         "root": True
            ...     }]
            ... })
            >>>
            >>> # Multi-file spec with separate schemas
            >>> client.create_spec({
            ...     "name": "Complex API",
            ...     "files": [
            ...         {"path": "openapi.yaml", "content": main_spec, "root": True},
            ...         {"path": "schemas/pet.json", "content": pet_schema},
            ...         {"path": "schemas/user.json", "content": user_schema}
            ...     ]
            ... })
        """
        workspace_id = workspace_id or self.config.workspace_id

        if not workspace_id:
            raise ValueError("workspace_id is required to create a spec. Set POSTMAN_WORKSPACE_ID in .env or pass workspace_id parameter.")

        endpoint = f"/specs?workspaceId={workspace_id}"

        # Build the request payload
        payload = {
            "name": spec_data["name"],
            "type": spec_data.get("type", "openapi:3")  # Default to OpenAPI 3.0
        }

        if "description" in spec_data:
            payload["description"] = spec_data["description"]

        # Add files
        files = spec_data.get("files", [])
        if not files:
            raise ValueError("At least one file must be provided in spec_data['files']")

        payload["files"] = []
        for i, file_obj in enumerate(files):
            file_entry = {
                "path": file_obj["path"],
                "content": file_obj["content"]
            }
            # Note: root is handled automatically by API based on type field
            payload["files"].append(file_entry)

        response = self._make_request('POST', endpoint, json=payload)
        return response.get('data', {})

    def list_specs(self, workspace_id=None, limit=10, offset=0):
        """
        List all API specifications in a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)
            limit: Maximum number of specs to return (default: 10)
            offset: Number of specs to skip (default: 0)

        Returns:
            List of spec objects

        Example:
            >>> specs = client.list_specs()
            >>> for spec in specs:
            ...     print(f"{spec['name']} - {spec['id']}")
        """
        workspace_id = workspace_id or self.config.workspace_id

        endpoint = "/specs"
        params = []

        if workspace_id:
            params.append(f"workspaceId={workspace_id}")
        if limit:
            params.append(f"limit={limit}")
        if offset:
            params.append(f"offset={offset}")

        if params:
            endpoint += "?" + "&".join(params)

        response = self._make_request('GET', endpoint)
        return response.get('data', [])

    def get_spec(self, spec_id):
        """
        Get detailed information about a specific API specification.

        Args:
            spec_id: Unique identifier for the spec

        Returns:
            Spec object with full details including files

        Example:
            >>> spec = client.get_spec("spec-12345")
            >>> print(f"Spec: {spec['name']}")
            >>> print(f"Files: {len(spec.get('files', []))}")
        """
        endpoint = f"/specs/{spec_id}"
        response = self._make_request('GET', endpoint)
        return response.get('data', {})

    def update_spec(self, spec_id, spec_data):
        """
        Update an existing API specification's metadata.

        Note: To update file contents, use update_spec_file() instead.

        Args:
            spec_id: Unique identifier for the spec
            spec_data: Dictionary containing fields to update:
                - name: New spec name (optional)
                - description: New description (optional)

        Returns:
            Updated spec object

        Example:
            >>> client.update_spec("spec-12345", {
            ...     "name": "Pet Store API v2",
            ...     "description": "Updated description"
            ... })
        """
        endpoint = f"/specs/{spec_id}"
        response = self._make_request('PATCH', endpoint, json=spec_data)
        return response.get('data', {})

    def delete_spec(self, spec_id):
        """
        Delete an API specification from Spec Hub.

        Args:
            spec_id: Unique identifier for the spec

        Returns:
            Deletion confirmation

        Example:
            >>> client.delete_spec("spec-12345")
        """
        endpoint = f"/specs/{spec_id}"
        response = self._make_request('DELETE', endpoint)
        return response

    def create_spec_file(self, spec_id, file_path, content, root=False):
        """
        Add a new file to an existing multi-file specification.

        Args:
            spec_id: Unique identifier for the spec
            file_path: Path for the new file (e.g., "schemas/pet.json")
            content: File content as string (JSON or YAML)
            root: Boolean, mark as root file (default: False)

        Returns:
            Created file object

        Example:
            >>> # Add a new schema file
            >>> client.create_spec_file(
            ...     spec_id="spec-12345",
            ...     file_path="schemas/order.json",
            ...     content=order_schema_json
            ... )
        """
        endpoint = f"/specs/{spec_id}/files"
        payload = {
            "path": file_path,
            "content": content
        }
        if root:
            payload["root"] = True

        response = self._make_request('POST', endpoint, json=payload)
        return response.get('data', {})

    def update_spec_file(self, spec_id, file_path, content=None, root=None):
        """
        Update an existing file in a specification.

        Note: You can update either content, root status, or both.

        Args:
            spec_id: Unique identifier for the spec
            file_path: Path of the file to update
            content: New file content (optional)
            root: New root status (optional)

        Returns:
            Updated file object

        Example:
            >>> # Update file content
            >>> client.update_spec_file(
            ...     spec_id="spec-12345",
            ...     file_path="openapi.yaml",
            ...     content=updated_yaml_content
            ... )
            >>>
            >>> # Change root file
            >>> client.update_spec_file(
            ...     spec_id="spec-12345",
            ...     file_path="openapi.yaml",
            ...     root=True
            ... )
        """
        endpoint = f"/specs/{spec_id}/files/{file_path}"
        payload = {}

        if content is not None:
            payload["content"] = content
        if root is not None:
            payload["root"] = root

        if not payload:
            raise ValueError("At least one of 'content' or 'root' must be provided")

        response = self._make_request('PATCH', endpoint, json=payload)
        return response.get('data', {})

    def delete_spec_file(self, spec_id, file_path):
        """
        Delete a file from a multi-file specification.

        Note: Cannot delete the root file if it's the only file.

        Args:
            spec_id: Unique identifier for the spec
            file_path: Path of the file to delete

        Returns:
            Deletion confirmation

        Example:
            >>> client.delete_spec_file("spec-12345", "schemas/deprecated.json")
        """
        endpoint = f"/specs/{spec_id}/files/{file_path}"
        response = self._make_request('DELETE', endpoint)
        return response

    def get_spec_files(self, spec_id):
        """
        List all files in a specification.

        Args:
            spec_id: Unique identifier for the spec

        Returns:
            List of file objects with paths and metadata

        Example:
            >>> files = client.get_spec_files("spec-12345")
            >>> for file in files:
            ...     print(f"{'[ROOT] ' if file.get('root') else ''}{file['path']}")
        """
        endpoint = f"/specs/{spec_id}/files"
        response = self._make_request('GET', endpoint)
        return response.get('data', [])

    def generate_collection_from_spec(self, spec_id, collection_name=None):
        """
        Generate a Postman collection from an API specification.

        Creates a collection with folders, requests, and examples based
        on the spec's endpoints and operations.

        Args:
            spec_id: Unique identifier for the spec
            collection_name: Name for the generated collection (optional)

        Returns:
            Generation task object with status and collection details

        Example:
            >>> result = client.generate_collection_from_spec("spec-12345")
            >>> if result.get('status') == 'completed':
            ...     collection_id = result['data']['collectionId']
            ...     print(f"Collection created: {collection_id}")
        """
        endpoint = f"/specs/{spec_id}/generations/collection"
        payload = {}

        if collection_name:
            payload["name"] = collection_name

        response = self._make_request('POST', endpoint, json=payload if payload else None)
        return response

    def list_collections_from_spec(self, spec_id):
        """
        List all collections generated from a specification.

        Args:
            spec_id: Unique identifier for the spec

        Returns:
            List of collection objects generated from this spec

        Example:
            >>> collections = client.list_collections_from_spec("spec-12345")
            >>> print(f"Found {len(collections)} collections generated from this spec")
        """
        endpoint = f"/specs/{spec_id}/generations/collection"
        response = self._make_request('GET', endpoint)
        return response.get('data', [])

    def generate_spec_from_collection(self, collection_id, spec_name=None, workspace_id=None):
        """
        Generate an API specification from an existing Postman collection.

        Reverse-engineers a spec from collection requests and responses.

        Args:
            collection_id: Collection UID to generate spec from
            spec_name: Name for the generated spec (optional)
            workspace_id: Workspace for the spec (uses config default if not provided)

        Returns:
            Generation task object with status and spec details

        Example:
            >>> result = client.generate_spec_from_collection("collection-12345")
            >>> if result.get('status') == 'completed':
            ...     spec_id = result['data']['specId']
            ...     print(f"Spec created: {spec_id}")
        """
        workspace_id = workspace_id or self.config.workspace_id

        endpoint = f"/collections/{collection_id}/generations/spec"
        payload = {}

        if spec_name:
            payload["name"] = spec_name
        if workspace_id:
            payload["workspace"] = workspace_id

        response = self._make_request('POST', endpoint, json=payload if payload else None)
        return response

    # Deploy Phase: Mock Server Operations

    def list_mocks(self, workspace_id=None):
        """
        List all mock servers in a workspace.

        Args:
            workspace_id: Workspace ID (uses config default if not provided)

        Returns:
            List of mock server objects
        """
        workspace_id = workspace_id or self.config.workspace_id

        if workspace_id:
            endpoint = f"/mocks?workspace={workspace_id}"
        else:
            endpoint = "/mocks"

        response = self._make_request('GET', endpoint)
        return response.get('mocks', [])

    def get_mock(self, mock_id):
        """
        Get detailed information about a specific mock server.

        Args:
            mock_id: Unique identifier for the mock server

        Returns:
            Mock server object with full details
        """
        endpoint = f"/mocks/{mock_id}"
        response = self._make_request('GET', endpoint)
        return response.get('mock', {})

    def create_mock(self, mock_data):
        """
        Create a new mock server.

        Args:
            mock_data: Dictionary containing mock server configuration:
                - name: Mock server name
                - collection: Collection UID
                - environment: Environment UID (optional)
                - private: Boolean, whether mock is private (optional)

        Returns:
            Created mock server object
        """
        endpoint = "/mocks"
        response = self._make_request('POST', endpoint, json={'mock': mock_data})
        return response.get('mock', {})

    def update_mock(self, mock_id, mock_data):
        """
        Update an existing mock server.

        Args:
            mock_id: Unique identifier for the mock server
            mock_data: Dictionary containing fields to update

        Returns:
            Updated mock server object
        """
        endpoint = f"/mocks/{mock_id}"
        response = self._make_request('PUT', endpoint, json={'mock': mock_data})
        return response.get('mock', {})

    def delete_mock(self, mock_id):
        """
        Delete a mock server.

        Args:
            mock_id: Unique identifier for the mock server

        Returns:
            Deletion confirmation
        """
        endpoint = f"/mocks/{mock_id}"
        response = self._make_request('DELETE', endpoint)
        return response
