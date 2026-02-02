"""
Configuration management for Postman Agent Skill.
Handles environment variables and provides validated configuration.
"""

import os
import sys
from pathlib import Path


def load_env_file():
    """
    Load environment variables from .env file in the skill directory.
    This ensures API keys are automatically loaded without user intervention.
    """
    # Find the .env file in the skill directory (parent of scripts/)
    script_dir = Path(__file__).parent
    skill_dir = script_dir.parent
    env_file = skill_dir / ".env"

    if not env_file.exists():
        return False

    # Try using python-dotenv if available (preferred method)
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        return True
    except ImportError:
        # Fallback: manually parse .env file
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#'):
                        continue
                    # Parse KEY=VALUE format
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        # Only set if not already in environment
                        if key and not os.getenv(key):
                            os.environ[key] = value
            return True
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}", file=sys.stderr)
            return False


# Load .env file when this module is imported
_env_loaded = load_env_file()


class PostmanConfig:
    """
    Manages configuration from environment variables.
    Validates required settings and provides defaults.
    """

    def __init__(self):
        # Required
        self.api_key = os.getenv("POSTMAN_API_KEY")

        # Optional with defaults
        self.workspace_id = os.getenv("POSTMAN_WORKSPACE_ID")
        self.rate_limit_delay = int(os.getenv("POSTMAN_RATE_LIMIT_DELAY", "60"))
        self.max_retries = int(os.getenv("POSTMAN_MAX_RETRIES", "3"))
        self.timeout = int(os.getenv("POSTMAN_TIMEOUT", "10"))

        # Proxy settings
        # By default, bypass all proxies to avoid "403 Forbidden" proxy errors
        # Set POSTMAN_USE_PROXY=true to enable proxy (if needed)
        use_proxy = os.getenv("POSTMAN_USE_PROXY", "false").lower() in ("true", "1", "yes")

        if not use_proxy:
            # Disable all proxies for direct connection
            self.proxies = {
                "http": None,
                "https": None,
            }
        else:
            # Use system/environment proxy settings
            self.proxies = None

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def validate(self):
        """
        Validate that required configuration is present.
        Raises ValueError with helpful message if configuration is invalid.
        """
        if not self.api_key:
            script_dir = Path(__file__).parent
            skill_dir = script_dir.parent
            env_file = skill_dir / ".env"

            error_msg = "POSTMAN_API_KEY not set.\n\n"

            if not env_file.exists():
                error_msg += (
                    "The .env file is missing from the skill package.\n\n"
                    "To fix this:\n"
                    "1. Create a .env file in the skill directory:\n"
                    f"   {skill_dir}\n"
                    "2. Add your Postman API key:\n"
                    "   POSTMAN_API_KEY=PMAK-your-key-here\n\n"
                    "To get your API key:\n"
                    "- Visit: https://web.postman.co/settings/me/api-keys\n"
                    "- Click 'Generate API Key'\n"
                    "- Copy the key (starts with 'PMAK-')\n"
                )
            else:
                error_msg += (
                    f"Found .env file at: {env_file}\n"
                    "But POSTMAN_API_KEY is not set or is empty.\n\n"
                    "Please check your .env file contains:\n"
                    "POSTMAN_API_KEY=PMAK-your-key-here\n\n"
                    "To get your API key:\n"
                    "- Visit: https://web.postman.co/settings/me/api-keys\n"
                    "- Click 'Generate API Key'\n"
                    "- Copy the key (starts with 'PMAK-')\n"
                )

            raise ValueError(error_msg)

        if not self.api_key.startswith("PMAK-"):
            raise ValueError(
                "Invalid POSTMAN_API_KEY format.\n"
                "API keys should start with 'PMAK-'\n"
                "Please check your key from: https://web.postman.co/settings/me/api-keys"
            )

    @property
    def base_url(self):
        """Base URL for Postman API"""
        return "https://api.getpostman.com"

    @property
    def headers(self):
        """HTTP headers for API requests"""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }


def get_config():
    """
    Get validated configuration instance.
    Exits with error message if configuration is invalid.
    """
    config = PostmanConfig()
    try:
        config.validate()
        return config
    except ValueError as e:
        print(f"Configuration Error: {e}", file=sys.stderr)
        sys.exit(1)
