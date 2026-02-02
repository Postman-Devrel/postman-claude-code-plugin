#!/usr/bin/env python3
"""
Generate code snippets from Postman collections and requests.

Generates client code in multiple languages for API requests including:
- curl
- Python (requests library)
- JavaScript (fetch API)
- Node.js (axios)
- Go (net/http)

Usage:
    python generate_code.py --collection <collection-id> --language python
    python generate_code.py --collection <collection-id> --all
    python generate_code.py --request <collection-id> <request-name> --language curl
    python generate_code.py --help
"""

import sys
import os
import argparse
import json
from urllib.parse import urlencode, urlparse, parse_qs

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


class CodeGenerator:
    """Generate code snippets from Postman requests."""

    @staticmethod
    def generate_curl(request, name=""):
        """Generate curl command."""
        method = request.get('method', 'GET')
        url = request.get('url', {})

        if isinstance(url, dict):
            url_str = url.get('raw', '')
        else:
            url_str = str(url)

        # Build curl command
        parts = ['curl']

        # Add method if not GET
        if method != 'GET':
            parts.extend(['-X', method])

        # Add headers
        headers = request.get('header', [])
        for header in headers:
            if not header.get('disabled', False):
                parts.extend(['-H', f'"{header.get("key")}: {header.get("value")}"'])

        # Add body
        body = request.get('body', {})
        if body:
            mode = body.get('mode', '')

            if mode == 'raw':
                raw_body = body.get('raw', '')
                parts.extend(['-d', f"'{raw_body}'"])

            elif mode == 'urlencoded':
                urlencoded = body.get('urlencoded', [])
                data = {item['key']: item['value'] for item in urlencoded if not item.get('disabled', False)}
                parts.extend(['-d', f"'{urlencode(data)}'"])

            elif mode == 'formdata':
                formdata = body.get('formdata', [])
                for item in formdata:
                    if not item.get('disabled', False):
                        parts.extend(['-F', f'"{item["key"]}={item["value"]}"'])

        # Add URL
        parts.append(f'"{url_str}"')

        return ' \\\n  '.join(parts)

    @staticmethod
    def generate_python(request, name=""):
        """Generate Python code using requests library."""
        method = request.get('method', 'GET').lower()
        url = request.get('url', {})

        if isinstance(url, dict):
            url_str = url.get('raw', '')
        else:
            url_str = str(url)

        code = []
        code.append("import requests")
        code.append("")

        # Headers
        headers = request.get('header', [])
        if headers:
            code.append("headers = {")
            for header in headers:
                if not header.get('disabled', False):
                    code.append(f'    "{header.get("key")}": "{header.get("value")}",')
            code.append("}")
            code.append("")

        # Body
        body = request.get('body', {})
        has_body = False

        if body:
            mode = body.get('mode', '')

            if mode == 'raw':
                raw_body = body.get('raw', '')
                try:
                    # Try to parse as JSON
                    json_body = json.loads(raw_body)
                    code.append("data = " + json.dumps(json_body, indent=4))
                    has_body = True
                except:
                    code.append(f"data = '''{raw_body}'''")
                    has_body = True
                code.append("")

            elif mode == 'urlencoded':
                urlencoded = body.get('urlencoded', [])
                code.append("data = {")
                for item in urlencoded:
                    if not item.get('disabled', False):
                        code.append(f'    "{item["key"]}": "{item["value"]}",')
                code.append("}")
                code.append("")
                has_body = True

        # Request
        params = []
        params.append(f'"{url_str}"')

        if headers:
            params.append("headers=headers")

        if has_body:
            if mode == 'raw' and body.get('options', {}).get('raw', {}).get('language') == 'json':
                params.append("json=data")
            else:
                params.append("data=data")

        code.append(f"response = requests.{method}(")
        code.append("    " + ",\n    ".join(params))
        code.append(")")
        code.append("")
        code.append("print(response.status_code)")
        code.append("print(response.json())")

        return "\n".join(code)

    @staticmethod
    def generate_javascript(request, name=""):
        """Generate JavaScript code using fetch API."""
        method = request.get('method', 'GET')
        url = request.get('url', {})

        if isinstance(url, dict):
            url_str = url.get('raw', '')
        else:
            url_str = str(url)

        code = []

        # Build fetch options
        code.append("const options = {")
        code.append(f'  method: "{method}",')

        # Headers
        headers = request.get('header', [])
        if headers:
            code.append("  headers: {")
            for header in headers:
                if not header.get('disabled', False):
                    code.append(f'    "{header.get("key")}": "{header.get("value")}",')
            code.append("  },")

        # Body
        body = request.get('body', {})
        if body and method != 'GET':
            mode = body.get('mode', '')

            if mode == 'raw':
                raw_body = body.get('raw', '')
                code.append(f"  body: `{raw_body}`,")

        code.append("};")
        code.append("")

        # Fetch call
        code.append(f'fetch("{url_str}", options)')
        code.append("  .then(response => response.json())")
        code.append("  .then(data => console.log(data))")
        code.append("  .catch(error => console.error('Error:', error));")

        return "\n".join(code)

    @staticmethod
    def generate_nodejs(request, name=""):
        """Generate Node.js code using axios."""
        method = request.get('method', 'GET').lower()
        url = request.get('url', {})

        if isinstance(url, dict):
            url_str = url.get('raw', '')
        else:
            url_str = str(url)

        code = []
        code.append("const axios = require('axios');")
        code.append("")

        # Build config
        code.append("const config = {")
        code.append(f'  method: "{method}",')
        code.append(f'  url: "{url_str}",')

        # Headers
        headers = request.get('header', [])
        if headers:
            code.append("  headers: {")
            for header in headers:
                if not header.get('disabled', False):
                    code.append(f'    "{header.get("key")}": "{header.get("value")}",')
            code.append("  },")

        # Body
        body = request.get('body', {})
        if body and method != 'get':
            mode = body.get('mode', '')

            if mode == 'raw':
                raw_body = body.get('raw', '')
                try:
                    json_body = json.loads(raw_body)
                    code.append(f"  data: {json.dumps(json_body, indent=4)},")
                except:
                    code.append(f'  data: `{raw_body}`,')

        code.append("};")
        code.append("")

        # Axios call
        code.append("axios(config)")
        code.append("  .then(response => {")
        code.append("    console.log(response.data);")
        code.append("  })")
        code.append("  .catch(error => {")
        code.append("    console.error(error);")
        code.append("  });")

        return "\n".join(code)

    @staticmethod
    def generate_go(request, name=""):
        """Generate Go code using net/http."""
        method = request.get('method', 'GET')
        url = request.get('url', {})

        if isinstance(url, dict):
            url_str = url.get('raw', '')
        else:
            url_str = str(url)

        code = []
        code.append("package main")
        code.append("")
        code.append("import (")
        code.append('\t"fmt"')
        code.append('\t"io"')
        code.append('\t"net/http"')

        # Check if we need strings package
        body = request.get('body', {})
        if body:
            code.append('\t"strings"')

        code.append(")")
        code.append("")
        code.append("func main() {")

        # Body
        if body:
            mode = body.get('mode', '')
            if mode == 'raw':
                raw_body = body.get('raw', '').replace('"', '\\"')
                code.append(f'\tpayload := strings.NewReader(`{raw_body}`)')
        else:
            code.append("\tpayload := nil")

        code.append("")

        # Create request
        code.append(f'\treq, _ := http.NewRequest("{method}", "{url_str}", payload)')
        code.append("")

        # Headers
        headers = request.get('header', [])
        if headers:
            for header in headers:
                if not header.get('disabled', False):
                    code.append(f'\treq.Header.Add("{header.get("key")}", "{header.get("value")}")')
            code.append("")

        # Execute request
        code.append("\tres, _ := http.DefaultClient.Do(req)")
        code.append("\tdefer res.Body.Close()")
        code.append("")
        code.append("\tbody, _ := io.ReadAll(res.Body)")
        code.append("\tfmt.Println(string(body))")
        code.append("}")

        return "\n".join(code)


def generate_from_collection(client, collection_id, language='all'):
    """Generate code snippets from all requests in a collection."""
    print(f"=== Generating Code for Collection ===\n")

    try:
        collection = client.get_collection(collection_id)
        collection_name = collection.get('info', {}).get('name', 'Unnamed')

        print(f"Collection: {collection_name}\n")

        def process_items(items, folder_path=""):
            """Process collection items recursively."""
            for item in items:
                if 'request' in item:
                    request = item['request']
                    name = item.get('name', 'Unnamed')
                    full_name = f"{folder_path}/{name}" if folder_path else name

                    print(f"\n{'=' * 70}")
                    print(f"Request: {full_name}")
                    print(f"Method: {request.get('method', 'GET')}")
                    print('=' * 70)

                    generator = CodeGenerator()

                    if language == 'all' or language == 'curl':
                        print("\n### curl ###\n")
                        print(generator.generate_curl(request, name))

                    if language == 'all' or language == 'python':
                        print("\n### Python ###\n")
                        print(generator.generate_python(request, name))

                    if language == 'all' or language == 'javascript':
                        print("\n### JavaScript ###\n")
                        print(generator.generate_javascript(request, name))

                    if language == 'all' or language == 'nodejs':
                        print("\n### Node.js ###\n")
                        print(generator.generate_nodejs(request, name))

                    if language == 'all' or language == 'go':
                        print("\n### Go ###\n")
                        print(generator.generate_go(request, name))

                elif 'item' in item:
                    folder = item.get('name', 'Folder')
                    new_path = f"{folder_path}/{folder}" if folder_path else folder
                    process_items(item['item'], new_path)

        process_items(collection.get('item', []))

    except Exception as e:
        print(f"Error generating code: {e}")
        sys.exit(1)


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description='Generate code snippets from Postman collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate Python code for all requests
  python generate_code.py --collection <collection-id> --language python

  # Generate all languages
  python generate_code.py --collection <collection-id> --all

  # Generate curl commands only
  python generate_code.py --collection <collection-id> --language curl

Languages: curl, python, javascript, nodejs, go
        """
    )

    parser.add_argument('--collection', metavar='COLLECTION_ID', required=True, help='Collection ID')
    parser.add_argument('--language', choices=['curl', 'python', 'javascript', 'nodejs', 'go'],
                       help='Programming language')
    parser.add_argument('--all', action='store_true', help='Generate code for all languages')

    args = parser.parse_args()

    if not args.language and not args.all:
        print("Error: Specify --language or --all")
        parser.print_help()
        return

    language = 'all' if args.all else args.language

    client = PostmanClient()
    generate_from_collection(client, args.collection, language)


if __name__ == '__main__':
    main()
