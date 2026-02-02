#!/usr/bin/env python3
"""
Security audit for Postman APIs and collections.

Performs comprehensive security analysis including:
- OpenAPI security definition validation
- Collection authentication checks
- HTTPS enforcement verification
- Security header analysis
- Sensitive data exposure checks
- Security best practices compliance

Usage:
    python audit_security.py --api <api-id>
    python audit_security.py --collection <collection-id>
    python audit_security.py --spec <spec-id>
    python audit_security.py --all
    python audit_security.py --help
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


class SecurityAuditor:
    """Security auditor for Postman resources."""

    def __init__(self, client):
        self.client = client
        self.findings = []
        self.severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    def add_finding(self, severity, category, message, recommendation=None):
        """Add a security finding."""
        finding = {
            "severity": severity,
            "category": category,
            "message": message,
            "recommendation": recommendation
        }
        self.findings.append(finding)
        self.severity_counts[severity] += 1

    def audit_openapi_security(self, spec_content):
        """Audit OpenAPI specification security definitions."""
        print("🔍 Auditing OpenAPI Security Definitions...\n")

        try:
            if isinstance(spec_content, str):
                spec = json.loads(spec_content)
            else:
                spec = spec_content

            # Check for security schemes
            security_schemes = spec.get('components', {}).get('securitySchemes', {})

            if not security_schemes:
                self.add_finding(
                    "high",
                    "Missing Security",
                    "No security schemes defined in OpenAPI spec",
                    "Add security schemes (OAuth2, API Key, JWT, etc.) in components.securitySchemes"
                )
            else:
                print(f"✓ Found {len(security_schemes)} security scheme(s)")
                for name, scheme in security_schemes.items():
                    scheme_type = scheme.get('type', 'unknown')
                    print(f"  - {name}: {scheme_type}")

                    # Check for insecure schemes
                    if scheme_type == 'http' and scheme.get('scheme') == 'basic':
                        self.add_finding(
                            "medium",
                            "Weak Authentication",
                            f"Basic authentication used in scheme '{name}'",
                            "Consider using OAuth2 or API keys with JWT"
                        )

            # Check global security requirements
            if 'security' not in spec:
                self.add_finding(
                    "medium",
                    "Missing Security",
                    "No global security requirements defined",
                    "Add top-level 'security' array to enforce authentication on all endpoints"
                )

            # Check endpoints for HTTPS
            servers = spec.get('servers', [])
            for server in servers:
                url = server.get('url', '')
                if url.startswith('http://') and 'localhost' not in url and '127.0.0.1' not in url:
                    self.add_finding(
                        "critical",
                        "Insecure Protocol",
                        f"Server uses HTTP instead of HTTPS: {url}",
                        "Use HTTPS for all production endpoints"
                    )

            # Check paths for security
            paths = spec.get('paths', {})
            unsecured_endpoints = []

            for path, methods in paths.items():
                for method, operation in methods.items():
                    if method not in ['get', 'post', 'put', 'delete', 'patch']:
                        continue

                    # Check if endpoint has security
                    endpoint_security = operation.get('security', spec.get('security', []))

                    if not endpoint_security or endpoint_security == [{}]:
                        unsecured_endpoints.append(f"{method.upper()} {path}")

            if unsecured_endpoints:
                self.add_finding(
                    "high",
                    "Unsecured Endpoints",
                    f"{len(unsecured_endpoints)} endpoint(s) have no authentication",
                    f"Add security requirements to: {', '.join(unsecured_endpoints[:3])}" +
                    (f" and {len(unsecured_endpoints) - 3} more" if len(unsecured_endpoints) > 3 else "")
                )

        except json.JSONDecodeError:
            self.add_finding(
                "info",
                "Parse Error",
                "Could not parse OpenAPI spec as JSON",
                None
            )
        except Exception as e:
            self.add_finding(
                "info",
                "Audit Error",
                f"Error auditing OpenAPI spec: {str(e)}",
                None
            )

    def audit_collection_security(self, collection):
        """Audit Postman collection security."""
        print("🔍 Auditing Collection Security...\n")

        # Check collection-level auth
        auth = collection.get('auth')

        if not auth or auth.get('type') == 'noauth':
            self.add_finding(
                "medium",
                "Missing Authentication",
                "Collection has no authentication configured",
                "Add collection-level authentication (API Key, Bearer Token, OAuth2, etc.)"
            )
        else:
            auth_type = auth.get('type', 'unknown')
            print(f"✓ Collection uses {auth_type} authentication")

            # Check for weak auth types
            if auth_type == 'basic':
                self.add_finding(
                    "medium",
                    "Weak Authentication",
                    "Collection uses Basic authentication",
                    "Consider using OAuth2 or API keys with JWT for better security"
                )

        # Check requests
        def check_requests(items, parent_auth=auth):
            """Recursively check requests in folders."""
            http_count = 0
            https_count = 0
            no_auth_count = 0

            for item in items:
                if 'request' in item:
                    request = item['request']

                    # Check URL protocol
                    url = request.get('url', {})
                    if isinstance(url, dict):
                        url_raw = url.get('raw', '')
                    else:
                        url_raw = url

                    if url_raw.startswith('http://') and 'localhost' not in url_raw and '127.0.0.1' not in url_raw:
                        http_count += 1

                    if url_raw.startswith('https://'):
                        https_count += 1

                    # Check request-level auth
                    request_auth = request.get('auth', parent_auth)

                    if not request_auth or request_auth.get('type') == 'noauth':
                        no_auth_count += 1

                    # Check for sensitive data in URL
                    if re.search(r'(api[_-]?key|token|password|secret)=', url_raw, re.IGNORECASE):
                        self.add_finding(
                            "critical",
                            "Sensitive Data Exposure",
                            f"Potential sensitive data in URL: {item.get('name', 'Unnamed request')}",
                            "Move sensitive data to headers or request body"
                        )

                    # Check headers for security
                    headers = request.get('header', [])
                    has_auth_header = any(
                        h.get('key', '').lower() in ['authorization', 'x-api-key', 'api-key']
                        for h in headers
                    )

                    # If no auth and no security headers, flag it
                    if not request_auth and not has_auth_header and not parent_auth:
                        # Skip if it's a GET to a public endpoint
                        if request.get('method', 'GET') != 'GET':
                            self.add_finding(
                                "medium",
                                "Unauthenticated Request",
                                f"Request '{item.get('name', 'Unnamed')}' has no authentication",
                                "Add authentication to prevent unauthorized access"
                            )

                elif 'item' in item:  # Folder
                    folder_auth = item.get('auth', parent_auth)
                    sub_http, sub_https, sub_no_auth = check_requests(item['item'], folder_auth)
                    http_count += sub_http
                    https_count += sub_https
                    no_auth_count += sub_no_auth

            return http_count, https_count, no_auth_count

        http_count, https_count, no_auth_count = check_requests(collection.get('item', []))

        # Report HTTP usage
        if http_count > 0:
            self.add_finding(
                "critical",
                "Insecure Protocol",
                f"{http_count} request(s) use HTTP instead of HTTPS",
                "Update all requests to use HTTPS"
            )
        else:
            print(f"✓ All requests use HTTPS")

        if no_auth_count > 0:
            self.add_finding(
                "info",
                "Unauthenticated Requests",
                f"{no_auth_count} request(s) have no authentication configured",
                "Review if these endpoints should be public"
            )

    def audit_api_security(self, api_id):
        """Audit a Postman API."""
        print(f"=== Security Audit: API {api_id} ===\n")

        try:
            # Get API details
            api = self.client.get_api(api_id)
            print(f"API: {api.get('name', 'Unnamed')}\n")

            # Get versions
            versions = self.client.get_api_versions(api_id)

            if not versions:
                self.add_finding(
                    "info",
                    "No Versions",
                    "API has no versions defined",
                    "Create at least one version with an OpenAPI schema"
                )
                return

            # Audit most recent version
            latest_version = versions[0]
            version_id = latest_version.get('id')

            print(f"Auditing version: {latest_version.get('name', 'Unknown')}\n")

            # Get schema
            schemas = self.client.get_api_schema(api_id, version_id)

            if schemas:
                schema = schemas[0]
                schema_content = schema.get('schema', '{}')
                self.audit_openapi_security(schema_content)
            else:
                self.add_finding(
                    "medium",
                    "Missing Schema",
                    f"API version '{latest_version.get('name')}' has no schema",
                    "Add an OpenAPI schema with security definitions"
                )

        except Exception as e:
            print(f"Error auditing API: {e}")
            sys.exit(1)

    def audit_spec_security(self, spec_id):
        """Audit a Spec Hub specification."""
        print(f"=== Security Audit: Spec {spec_id} ===\n")

        try:
            spec = self.client.get_spec(spec_id)
            print(f"Spec: {spec.get('name', 'Unnamed')}\n")

            files = spec.get('files', [])

            if not files:
                self.add_finding(
                    "info",
                    "No Files",
                    "Spec has no files",
                    None
                )
                return

            # Audit root file
            root_file = next((f for f in files if f.get('root')), files[0])
            spec_content = root_file.get('content', '{}')

            self.audit_openapi_security(spec_content)

        except Exception as e:
            print(f"Error auditing spec: {e}")
            sys.exit(1)

    def audit_collection_security_by_id(self, collection_id):
        """Audit a collection by ID."""
        print(f"=== Security Audit: Collection {collection_id} ===\n")

        try:
            collection = self.client.get_collection(collection_id)
            print(f"Collection: {collection.get('info', {}).get('name', 'Unnamed')}\n")

            self.audit_collection_security(collection)

        except Exception as e:
            print(f"Error auditing collection: {e}")
            sys.exit(1)

    def print_report(self):
        """Print security audit report."""
        print("\n" + "=" * 70)
        print("🛡️  SECURITY AUDIT REPORT")
        print("=" * 70 + "\n")

        # Summary
        total_findings = len(self.findings)
        print(f"Total Findings: {total_findings}\n")

        if total_findings == 0:
            print("✅ No security issues found!\n")
            return

        # Severity breakdown
        print("Severity Breakdown:")
        for severity in ["critical", "high", "medium", "low", "info"]:
            count = self.severity_counts[severity]
            if count > 0:
                emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵", "info": "⚪"}
                print(f"  {emoji[severity]} {severity.upper()}: {count}")
        print()

        # Group findings by severity
        for severity in ["critical", "high", "medium", "low", "info"]:
            severity_findings = [f for f in self.findings if f['severity'] == severity]

            if severity_findings:
                print(f"\n{severity.upper()} Severity:")
                print("-" * 70)

                for i, finding in enumerate(severity_findings, 1):
                    print(f"\n{i}. [{finding['category']}] {finding['message']}")
                    if finding['recommendation']:
                        print(f"   💡 Recommendation: {finding['recommendation']}")

        # Security score
        print("\n" + "=" * 70)
        score = max(0, 100 - (
            self.severity_counts['critical'] * 20 +
            self.severity_counts['high'] * 10 +
            self.severity_counts['medium'] * 5 +
            self.severity_counts['low'] * 2
        ))
        print(f"Security Score: {score}/100")

        if score >= 90:
            print("Grade: A (Excellent) ✅")
        elif score >= 75:
            print("Grade: B (Good) ✔️")
        elif score >= 60:
            print("Grade: C (Fair) ⚠️")
        elif score >= 40:
            print("Grade: D (Poor) ❌")
        else:
            print("Grade: F (Critical) 🔴")

        print("=" * 70 + "\n")


def main():
    """Main entry point for security audit."""

    parser = argparse.ArgumentParser(
        description='Security audit for Postman APIs and collections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Audit an API
  python audit_security.py --api abc-123

  # Audit a collection
  python audit_security.py --collection col-456

  # Audit a Spec Hub specification
  python audit_security.py --spec spec-789

  # Audit all collections in workspace
  python audit_security.py --all-collections

  # Audit all APIs in workspace
  python audit_security.py --all-apis
        """
    )

    parser.add_argument('--api', metavar='API_ID', help='Audit a specific API')
    parser.add_argument('--collection', metavar='COLLECTION_ID', help='Audit a specific collection')
    parser.add_argument('--spec', metavar='SPEC_ID', help='Audit a Spec Hub specification')
    parser.add_argument('--all-collections', action='store_true', help='Audit all collections')
    parser.add_argument('--all-apis', action='store_true', help='Audit all APIs')

    args = parser.parse_args()

    if not any([args.api, args.collection, args.spec, args.all_collections, args.all_apis]):
        parser.print_help()
        return

    # Initialize
    client = PostmanClient()
    auditor = SecurityAuditor(client)

    # Execute audit
    if args.api:
        auditor.audit_api_security(args.api)

    elif args.collection:
        auditor.audit_collection_security_by_id(args.collection)

    elif args.spec:
        auditor.audit_spec_security(args.spec)

    elif args.all_collections:
        collections = client.list_collections()
        print(f"Auditing {len(collections)} collection(s)...\n")
        for col in collections:
            auditor.audit_collection_security_by_id(col.get('uid'))
            print()

    elif args.all_apis:
        apis = client.list_apis()
        print(f"Auditing {len(apis)} API(s)...\n")
        for api in apis:
            auditor.audit_api_security(api.get('id'))
            print()

    # Print report
    auditor.print_report()


if __name__ == '__main__':
    main()
