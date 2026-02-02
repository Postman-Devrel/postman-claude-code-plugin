"""
Retry handler with exponential backoff for Postman API calls.
"""

import time
import sys


class RetryHandler:
    """Handles retry logic with exponential backoff for API calls"""

    def __init__(self, max_retries=3, base_delay=1):
        self.max_retries = max_retries
        self.base_delay = base_delay

    def should_retry(self, status_code):
        """Determine if a request should be retried based on status code"""
        # Retry on rate limits and server errors
        return status_code in [429, 500, 502, 503, 504]

    def get_delay(self, attempt):
        """Calculate exponential backoff delay"""
        return self.base_delay * (2 ** attempt)

    def execute(self, func, *args, **kwargs):
        """
        Execute a function with retry logic.

        Args:
            func: Function to execute (should return a requests.Response)
            *args, **kwargs: Arguments to pass to the function

        Returns:
            Response object from successful request

        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                response = func(*args, **kwargs)

                # Check if we should retry
                if self.should_retry(response.status_code):
                    if attempt < self.max_retries - 1:
                        delay = self.get_delay(attempt)
                        print(
                            f"Rate limited or server error (status {response.status_code}). "
                            f"Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})",
                            file=sys.stderr
                        )
                        time.sleep(delay)
                        continue
                    else:
                        raise Exception(
                            f"Max retries ({self.max_retries}) exceeded. "
                            f"Last status code: {response.status_code}"
                        )

                # Success or non-retryable error
                return response

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    delay = self.get_delay(attempt)
                    print(
                        f"Request failed: {e}. "
                        f"Retrying in {delay}s... (attempt {attempt + 1}/{self.max_retries})",
                        file=sys.stderr
                    )
                    time.sleep(delay)
                else:
                    raise

        # Should not reach here, but raise last exception if we do
        raise last_exception
