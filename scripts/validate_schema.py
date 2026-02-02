#!/usr/bin/env python3
"""
Validate OpenAPI and API specifications for correctness and best practices.

Performs comprehensive validation including:
- OpenAPI 3.0 specification compliance
- Schema structure validation
- Required fields checking
- Best practices recommendations

Usage:
    python validate_schema.py --api <api-id>
    python validate_schema.py --spec <spec-id>
    python validate_schema.py --file <openapi.json>
    python validate_schema.py --help
"""

import sys
import os
import argparse
import json
import re
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.postman_client import PostmanClient
from scripts.config import PostmanConfig


class SchemaValidator:
    """OpenAPI schema validator."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.info = []

    def add_error(self, message, location=""):
        """Add a validation error."""
        self.errors.append({"location": location, "message": message})

    def add_warning(self, message, location=""):
        """Add a validation warning."""
        self.warnings.append({"location": location, "message": message})

    def add_info(self, message, location=""):
        """Add validation info."""
        self.info.append({"location": location, "message": message})

    def validate_openapi_structure(self, spec):
        """Validate basic OpenAPI structure."""
        print("🔍 Validating OpenAPI Structure...\n")

        # Check OpenAPI version
        if 'openapi' not in spec:
            self.add_error("Missing 'openapi' version field", "root")
        else:
            version = spec['openapi']
            if not version.startswith('3.0'):
                self.add_warning(f"OpenAPI version {version} - recommend 3.0.x", "openapi")
            else:
                print(f"✓ OpenAPI version: {version}")

        # Check required root fields
        required_fields = ['info', 'paths']
        for field in required_fields:
            if field not in spec:
                self.add_error(f"Missing required field '{field}'", "root")

        # Validate info object
        if 'info' in spec:
            info = spec['info']
            if 'title' not in info:
                self.add_error("Missing 'title' in info", "info")
            if 'version' not in info:
                self.add_error("Missing 'version' in info", "info")

            # Check for description
            if 'description' not in info:
                self.add_warning("No description in info object", "info")

            # Check for contact/license
            if 'contact' not in info:
                self.add_info("Consider adding contact information", "info")
            if 'license' not in info:
                self.add_info("Consider adding license information", "info")

        # Check servers
        if 'servers' not in spec:
            self.add_warning("No servers defined", "root")
        else:
            print(f"✓ Found {len(spec['servers'])} server(s)")

    def validate_paths(self, spec):
        """Validate API paths."""
        print("\n🔍 Validating Paths...\n")

        paths = spec.get('paths', {})

        if not paths:
            self.add_error("No paths defined in specification", "paths")
            return

        print(f"✓ Found {len(paths)} path(s)")

        # Track operations
        operations_count = defaultdict(int)

        for path, methods in paths.items():
            # Check path format
            if not path.startswith('/'):
                self.add_error(f"Path must start with '/': {path}", f"paths.{path}")

            # Check for path parameters
            path_params = re.findall(r'{([^}]+)}', path)

            for method, operation in methods.items():
                if method not in ['get', 'post', 'put', 'delete', 'patch', 'head', 'options']:
                    continue

                operations_count[method.upper()] += 1
                location = f"paths.{path}.{method}"

                # Check for operationId
                if 'operationId' not in operation:
                    self.add_warning(f"Missing operationId", location)

                # Check for summary
                if 'summary' not in operation:
                    self.add_warning(f"Missing summary", location)

                # Check for tags
                if 'tags' not in operation:
                    self.add_info(f"No tags defined", location)

                # Validate path parameters are defined
                if path_params:
                    params = operation.get('parameters', [])
                    param_names = {p['name'] for p in params if p.get('in') == 'path'}

                    for path_param in path_params:
                        if path_param not in param_names:
                            self.add_error(
                                f"Path parameter '{path_param}' not defined in parameters",
                                location
                            )

                # Check request body for POST/PUT/PATCH
                if method in ['post', 'put', 'patch']:
                    if 'requestBody' not in operation:
                        self.add_warning(
                            f"{method.upper()} operation typically has a request body",
                            location
                        )

                # Check responses
                if 'responses' not in operation:
                    self.add_error(f"Missing responses", location)
                else:
                    responses = operation['responses']

                    # Check for success response
                    has_success = any(
                        code.startswith('2') for code in responses.keys()
                    )
                    if not has_success:
                        self.add_warning(f"No success response (2xx) defined", location)

                    # Check for error responses
                    has_error = any(
                        code.startswith('4') or code.startswith('5')
                        for code in responses.keys()
                    )
                    if not has_error:
                        self.add_info(f"Consider adding error responses (4xx, 5xx)", location)

        # Print operation summary
        print(f"\nOperation Summary:")
        for method, count in sorted(operations_count.items()):
            print(f"  {method}: {count}")

    def validate_components(self, spec):
        """Validate components/schemas."""
        print("\n🔍 Validating Components...\n")

        components = spec.get('components', {})

        if not components:
            self.add_warning("No components defined", "components")
            return

        # Check schemas
        schemas = components.get('schemas', {})
        if schemas:
            print(f"✓ Found {len(schemas)} schema(s)")

            for schema_name, schema in schemas.items():
                location = f"components.schemas.{schema_name}"

                # Check type
                if 'type' not in schema and '$ref' not in schema:
                    self.add_warning(f"Schema missing 'type' field", location)

                # Check for description
                if 'description' not in schema:
                    self.add_info(f"Consider adding description", location)

                # For object types, check properties
                if schema.get('type') == 'object':
                    if 'properties' not in schema:
                        self.add_warning(f"Object schema has no properties", location)

        # Check security schemes
        security_schemes = components.get('securitySchemes', {})
        if security_schemes:
            print(f"✓ Found {len(security_schemes)} security scheme(s)")
        else:
            self.add_warning("No security schemes defined", "components.securitySchemes")

    def validate_spec(self, spec):
        """Run all validations."""
        self.validate_openapi_structure(spec)
        self.validate_paths(spec)
        self.validate_components(spec)

    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 70)
        print("📋 VALIDATION REPORT")
        print("=" * 70 + "\n")

        total = len(self.errors) + len(self.warnings) + len(self.info)

        if total == 0:
            print("✅ Schema is valid! No issues found.\n")
            return

        # Summary
        print(f"Summary:")
        print(f"  🔴 Errors: {len(self.errors)}")
        print(f"  🟡 Warnings: {len(self.warnings)}")
        print(f"  🔵 Info: {len(self.info)}")
        print()

        # Errors
        if self.errors:
            print("🔴 ERRORS (Must Fix):")
            print("-" * 70)
            for i, error in enumerate(self.errors, 1):
                loc = f" [{error['location']}]" if error['location'] else ""
                print(f"{i}. {error['message']}{loc}")
            print()

        # Warnings
        if self.warnings:
            print("🟡 WARNINGS (Should Fix):")
            print("-" * 70)
            for i, warning in enumerate(self.warnings, 1):
                loc = f" [{warning['location']}]" if warning['location'] else ""
                print(f"{i}. {warning['message']}{loc}")
            print()

        # Info
        if self.info:
            print("🔵 RECOMMENDATIONS:")
            print("-" * 70)
            for i, info in enumerate(self.info, 1):
                loc = f" [{info['location']}]" if info['location'] else ""
                print(f"{i}. {info['message']}{loc}")
            print()

        # Score
        score = max(0, 100 - (len(self.errors) * 10) - (len(self.warnings) * 3))
        print("=" * 70)
        print(f"Validation Score: {score}/100")

        if score >= 90:
            print("Grade: A (Excellent) ✅")
        elif score >= 75:
            print("Grade: B (Good) ✔️")
        elif score >= 60:
            print("Grade: C (Fair) ⚠️")
        else:
            print("Grade: D (Needs Work) ❌")

        print("=" * 70 + "\n")


def validate_from_api(client, api_id):
    """Validate schema from Postman API."""
    print(f"=== Validating API: {api_id} ===\n")

    try:
        # Get API
        api = client.get_api(api_id)
        print(f"API: {api.get('name', 'Unnamed')}\n")

        # Get latest version
        versions = client.get_api_versions(api_id)
        if not versions:
            print("❌ No versions found for this API")
            return

        version = versions[0]
        print(f"Version: {version.get('name', 'Unknown')}\n")

        # Get schema
        schemas = client.get_api_schema(api_id, version.get('id'))
        if not schemas:
            print("❌ No schema found for this version")
            return

        schema_content = schemas[0].get('schema', '{}')
        spec = json.loads(schema_content)

        # Validate
        validator = SchemaValidator()
        validator.validate_spec(spec)
        validator.print_report()

    except Exception as e:
        print(f"❌ Error validating API: {e}")
        sys.exit(1)


def validate_from_spec(client, spec_id):
    """Validate schema from Spec Hub."""
    print(f"=== Validating Spec: {spec_id} ===\n")

    try:
        spec_data = client.get_spec(spec_id)
        print(f"Spec: {spec_data.get('name', 'Unnamed')}\n")

        files = spec_data.get('files', [])
        if not files:
            print("❌ No files found in spec")
            return

        # Get root file
        root_file = next((f for f in files if f.get('root')), files[0])
        spec_content = root_file.get('content', '{}')
        spec = json.loads(spec_content)

        # Validate
        validator = SchemaValidator()
        validator.validate_spec(spec)
        validator.print_report()

    except Exception as e:
        print(f"❌ Error validating spec: {e}")
        sys.exit(1)


def validate_from_file(file_path):
    """Validate schema from file."""
    print(f"=== Validating File: {file_path} ===\n")

    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                try:
                    import yaml
                    spec = yaml.safe_load(f)
                except ImportError:
                    print("❌ PyYAML not installed. Install with: pip install pyyaml")
                    sys.exit(1)
            else:
                spec = json.load(f)

        # Validate
        validator = SchemaValidator()
        validator.validate_spec(spec)
        validator.print_report()

    except Exception as e:
        print(f"❌ Error validating file: {e}")
        sys.exit(1)


def main():
    """Main entry point."""

    parser = argparse.ArgumentParser(
        description='Validate OpenAPI specifications',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate API schema
  python validate_schema.py --api <api-id>

  # Validate Spec Hub specification
  python validate_schema.py --spec <spec-id>

  # Validate local file
  python validate_schema.py --file openapi.json
        """
    )

    parser.add_argument('--api', metavar='API_ID', help='Validate API schema')
    parser.add_argument('--spec', metavar='SPEC_ID', help='Validate Spec Hub specification')
    parser.add_argument('--file', metavar='FILE_PATH', help='Validate local OpenAPI file')

    args = parser.parse_args()

    if not any([args.api, args.spec, args.file]):
        parser.print_help()
        return

    # Execute validation
    if args.api:
        client = PostmanClient()
        validate_from_api(client, args.api)

    elif args.spec:
        client = PostmanClient()
        validate_from_spec(client, args.spec)

    elif args.file:
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        validate_from_file(args.file)


if __name__ == '__main__':
    main()
