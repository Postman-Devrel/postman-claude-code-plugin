"""
Custom exception classes for Postman API errors.

Provides specific exception types for different API error scenarios,
with helpful error messages and resolution guidance.
"""


class PostmanAPIError(Exception):
    """
    Base exception for all Postman API errors.

    Attributes:
        message: Error message
        status_code: HTTP status code (if applicable)
        response_data: Raw API response data (if available)
    """

    def __init__(self, message, status_code=None, response_data=None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)

    def __str__(self):
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AuthenticationError(PostmanAPIError):
    """
    API key is invalid or missing.

    Raised when authentication fails (401 Unauthorized).
    """

    def __init__(self, message=None, status_code=401, response_data=None):
        if not message:
            message = (
                "Authentication failed. Your API key may be invalid or missing.\n\n"
                "To get a valid API key:\n"
                "1. Go to https://web.postman.co/settings/me/api-keys\n"
                "2. Click 'Generate API Key'\n"
                "3. Copy the key (starts with 'PMAK-')\n"
                "4. Set it as environment variable:\n"
                "   export POSTMAN_API_KEY='your-key-here'\n\n"
                "Or check that your current key hasn't expired."
            )
        super().__init__(message, status_code, response_data)


class RateLimitError(PostmanAPIError):
    """
    API rate limit exceeded.

    Raised when the client exceeds the Postman API rate limit (429 Too Many Requests).

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header)
    """

    def __init__(self, message=None, retry_after=None, status_code=429, response_data=None):
        self.retry_after = retry_after

        if not message:
            message = "API rate limit exceeded."
            if retry_after:
                message += f" Please wait {retry_after} seconds before retrying."
            else:
                message += " Please wait a few moments before retrying."

            message += (
                "\n\nTips to avoid rate limiting:\n"
                "- Reduce request frequency\n"
                "- Implement exponential backoff\n"
                "- Cache responses when possible\n"
                "- Upgrade to a higher plan for increased limits"
            )

        super().__init__(message, status_code, response_data)


class ResourceNotFoundError(PostmanAPIError):
    """
    Requested resource doesn't exist.

    Raised when the requested resource (collection, environment, API, etc.)
    is not found (404 Not Found).
    """

    def __init__(self, resource_type=None, resource_id=None, message=None,
                 status_code=404, response_data=None):
        self.resource_type = resource_type
        self.resource_id = resource_id

        if not message:
            if resource_type and resource_id:
                message = f"{resource_type} with ID '{resource_id}' was not found."
            else:
                message = "The requested resource was not found."

            message += (
                "\n\nPossible reasons:\n"
                "- The resource was deleted\n"
                "- The ID is incorrect\n"
                "- You don't have permission to access it\n"
                "- The resource is in a different workspace"
            )

        super().__init__(message, status_code, response_data)


class ValidationError(PostmanAPIError):
    """
    Request data failed validation.

    Raised when the API request contains invalid data (400 Bad Request).
    """

    def __init__(self, message=None, validation_errors=None,
                 status_code=400, response_data=None):
        self.validation_errors = validation_errors or []

        if not message:
            message = "Request validation failed."

            if self.validation_errors:
                message += "\n\nValidation errors:\n"
                for error in self.validation_errors:
                    message += f"  - {error}\n"
            else:
                message += " Please check your request data."

        super().__init__(message, status_code, response_data)


class PermissionError(PostmanAPIError):
    """
    Insufficient permissions for this operation.

    Raised when the user doesn't have permission to perform the requested
    operation (403 Forbidden).
    """

    def __init__(self, message=None, required_permission=None,
                 status_code=403, response_data=None):
        self.required_permission = required_permission

        if not message:
            message = "You don't have permission to perform this operation."

            if required_permission:
                message += f"\n\nRequired permission: {required_permission}"

            message += (
                "\n\nPossible solutions:\n"
                "- Check your workspace role/permissions\n"
                "- Request access from the workspace admin\n"
                "- Verify your API key has the necessary scopes\n"
                "- Ensure you're using the correct workspace ID"
            )

        super().__init__(message, status_code, response_data)


class DeprecatedEndpointError(PostmanAPIError):
    """
    Using a deprecated API endpoint.

    Raised when the skill detects use of a deprecated endpoint.
    """

    def __init__(self, endpoint, replacement=None, message=None,
                 status_code=None, response_data=None):
        self.endpoint = endpoint
        self.replacement = replacement

        if not message:
            message = f"Endpoint '{endpoint}' is deprecated."

            if replacement:
                message += f"\n\nPlease use '{replacement}' instead."

            message += (
                "\n\nDeprecated endpoints may be removed in future API versions. "
                "Update your code to use the recommended replacement."
            )

        super().__init__(message, status_code, response_data)


class ConflictError(PostmanAPIError):
    """
    Request conflicts with current state.

    Raised when the request conflicts with existing data (409 Conflict).
    For example, trying to create a resource that already exists.
    """

    def __init__(self, message=None, status_code=409, response_data=None):
        if not message:
            message = (
                "Request conflicts with existing data.\n\n"
                "Common causes:\n"
                "- Resource with this name already exists\n"
                "- Resource is in use and cannot be modified\n"
                "- Concurrent modification conflict"
            )

        super().__init__(message, status_code, response_data)


class ServerError(PostmanAPIError):
    """
    Postman API server error.

    Raised when the Postman API returns a server error (5xx status codes).
    """

    def __init__(self, message=None, status_code=500, response_data=None):
        if not message:
            message = (
                "Postman API server error. This is typically a temporary issue.\n\n"
                "Recommended actions:\n"
                "- Wait a few moments and retry\n"
                "- Check Postman status page: https://status.postman.com\n"
                "- If the issue persists, contact Postman support"
            )

        super().__init__(message, status_code, response_data)


class APIVersionError(PostmanAPIError):
    """
    API version incompatibility.

    Raised when the detected API version doesn't support the requested feature.
    """

    def __init__(self, feature, required_version=None, detected_version=None,
                 message=None):
        self.feature = feature
        self.required_version = required_version
        self.detected_version = detected_version

        if not message:
            message = f"Feature '{feature}' is not available."

            if required_version:
                message += f"\n\nRequired API version: {required_version}"

            if detected_version:
                message += f"\nDetected API version: {detected_version}"

            message += (
                "\n\nThis feature requires a newer version of the Postman API. "
                "Please upgrade to Postman v10+ for full compatibility."
            )

        super().__init__(message)


class NetworkError(PostmanAPIError):
    """
    Network connectivity error.

    Raised when unable to connect to the Postman API due to network issues.
    """

    def __init__(self, message=None, original_error=None):
        self.original_error = original_error

        if not message:
            message = "Failed to connect to Postman API."

            if original_error:
                error_str = str(original_error)
                message += f"\n\nOriginal error: {error_str}"

                # Detect DNS resolution errors (Claude Desktop network allowlist)
                if "NameResolutionError" in error_str or "Failed to resolve" in error_str or "Temporary failure in name resolution" in error_str:
                    message += (
                        "\n\n⚠️  DNS RESOLUTION ERROR - NETWORK RESTRICTION DETECTED"
                        "\n\n**This skill cannot run in Claude Desktop** due to network security restrictions."
                        "\n\nClaude Desktop only allows connections to these domains:"
                        "\n- api.anthropic.com"
                        "\n- github.com / pypi.org / npmjs.com"
                        "\n- archive.ubuntu.com / security.ubuntu.com"
                        "\n\n'api.getpostman.com' is NOT in the allowlist."
                        "\n\nSOLUTIONS:"
                        "\n1. Use the Claude API with code execution (fully supported)"
                        "\n2. Run the scripts directly on your local machine:"
                        "\n   python scripts/list_collections.py"
                        "\n3. Contact Anthropic to request adding api.getpostman.com to the allowlist"
                        "\n\nSee SKILL.md for details on environment compatibility."
                    )
                    return super().__init__(message)

                # Detect proxy-related errors
                if "ProxyError" in error_str or "Tunnel connection failed" in error_str or "403 Forbidden" in error_str:
                    message += (
                        "\n\n⚠️  PROXY ERROR DETECTED"
                        "\n\nThe connection is being blocked by a proxy server."
                        "\n\nSOLUTION: The skill now bypasses proxies by default."
                        "\n\nIf you're still seeing this error:"
                        "\n1. Ensure you have the latest version of the skill"
                        "\n2. The .env file should NOT contain POSTMAN_USE_PROXY=true"
                        "\n3. If in a corporate environment, you may need to:"
                        "\n   - Disable Claude Desktop's proxy settings"
                        "\n   - Or configure your proxy to allow api.getpostman.com"
                        "\n   - Or use a direct internet connection"
                    )
                    return super().__init__(message)

            message += (
                "\n\nPossible causes:\n"
                "- No internet connection\n"
                "- Proxy server blocking requests (see proxy error above)\n"
                "- Firewall blocking requests\n"
                "- Postman API is down (check https://status.postman.com)\n"
                "- DNS resolution issues"
            )

        super().__init__(message)


class TimeoutError(PostmanAPIError):
    """
    Request timeout error.

    Raised when the API request times out.
    """

    def __init__(self, message=None, timeout_seconds=None):
        self.timeout_seconds = timeout_seconds

        if not message:
            message = "API request timed out."

            if timeout_seconds:
                message += f"\n\nTimeout limit: {timeout_seconds} seconds"

            message += (
                "\n\nPossible solutions:\n"
                "- Increase timeout value in configuration\n"
                "- Check network connectivity\n"
                "- Try again later (API may be slow)\n"
                "- For large collections, consider pagination"
            )

        super().__init__(message)


# Helper function to create appropriate exception from response
def create_exception_from_response(response, default_message="API request failed"):
    """
    Create an appropriate exception based on HTTP status code and response data.

    Args:
        response: requests.Response object
        default_message: Default message if no specific error found

    Returns:
        An instance of the appropriate exception class
    """
    status_code = response.status_code

    # Try to parse error response
    try:
        error_data = response.json()
        error_info = error_data.get('error', {})
        message = error_info.get('message', default_message)
        error_name = error_info.get('name', '')
    except:
        error_data = None
        message = default_message
        error_name = ''

    # Map status codes to exceptions
    if status_code == 401:
        return AuthenticationError(message, status_code, error_data)

    elif status_code == 403:
        return PermissionError(message, status_code=status_code, response_data=error_data)

    elif status_code == 404:
        return ResourceNotFoundError(
            message=message,
            status_code=status_code,
            response_data=error_data
        )

    elif status_code == 400:
        # Try to extract validation errors
        validation_errors = []
        if error_data and 'error' in error_data:
            details = error_data['error'].get('details', [])
            validation_errors = [d.get('message', str(d)) for d in details]

        return ValidationError(
            message=message,
            validation_errors=validation_errors,
            status_code=status_code,
            response_data=error_data
        )

    elif status_code == 409:
        return ConflictError(message, status_code, error_data)

    elif status_code == 429:
        # Try to get retry-after header
        retry_after = response.headers.get('Retry-After')
        if retry_after:
            try:
                retry_after = int(retry_after)
            except:
                retry_after = None

        return RateLimitError(
            message=message,
            retry_after=retry_after,
            status_code=status_code,
            response_data=error_data
        )

    elif status_code >= 500:
        return ServerError(message, status_code, error_data)

    else:
        # Generic error for other status codes
        return PostmanAPIError(message, status_code, error_data)
