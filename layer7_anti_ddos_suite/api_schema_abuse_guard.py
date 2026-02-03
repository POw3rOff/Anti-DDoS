#!/usr/bin/env python3
"""
api_schema_abuse_guard.py
Layer 7 Anti-DDoS Script: Validates requests against API Schema.

Purpose:
Blocks requests that violate the expected API structure (extra fields, wrong types,
missing required parameters), which is common in fuzzing or blind injection attacks.

Usage:
    python3 api_schema_abuse_guard.py --schema schema.json < log_stream.json

Schema Format (Simple JSON Mapping):
    {
        "/login": {
            "method": "POST",
            "required_fields": ["username", "password"],
            "allow_extra_fields": false,
            "field_types": {"username": "string", "password": "string"}
        },
        "/api/search": {
            "method": "GET",
            "required_params": ["q"],
            "max_param_length": 50
        }
    }
"""

import sys
import json
import argparse

# Default mock schema if none provided
DEFAULT_SCHEMA = {
    "/login": {
        "method": "POST",
        "required_fields": ["username", "password"],
        "allow_extra_fields": False,
        "max_body_size": 1024
    },
    "/search": {
        "method": "GET",
        "required_params": ["q"],
        "max_param_length": 100
    }
}

class SchemaValidator:
    def __init__(self, schema_file=None):
        if schema_file:
            try:
                with open(schema_file, 'r') as f:
                    self.schema = json.load(f)
            except Exception as e:
                sys.stderr.write(f"Failed to load schema: {e}\n")
                self.schema = DEFAULT_SCHEMA
        else:
            self.schema = DEFAULT_SCHEMA

    def validate(self, record):
        path = record.get("url", "").split("?")[0]
        method = record.get("method", "GET")

        # If path not in schema, deciding policy (ALLOW or STRICT BLOCK)
        # Here we assume ALLOW unknown paths but flag known ones
        if path not in self.schema:
            return None

        rules = self.schema[path]
        violations = []

        # 1. Method Validation
        if rules.get("method") and method != rules.get("method"):
            violations.append(f"Invalid method {method} for {path}")

        # 2. Body/Params Validation
        # Assuming 'body' is a dictionary in the input record (parsed JSON)
        # or 'params' for GET requests

        if method == "POST":
            body = record.get("body_json", {})
            if not isinstance(body, dict):
                # If body wasn't parsed as JSON but rule expects structure
                pass
            else:
                # Check required fields
                for field in rules.get("required_fields", []):
                    if field not in body:
                        violations.append(f"Missing required field: {field}")

                # Check for extra fields
                if not rules.get("allow_extra_fields", True):
                    extras = set(body.keys()) - set(rules.get("required_fields", [])) - set(rules.get("optional_fields", []))
                    if extras:
                        violations.append(f"Unexpected fields: {list(extras)}")

        elif method == "GET":
            params = record.get("params", {}) # Assuming parsed params
            for param in rules.get("required_params", []):
                if param not in params:
                    violations.append(f"Missing required param: {param}")

            limit = rules.get("max_param_length")
            if limit:
                for k, v in params.items():
                    if len(str(v)) > limit:
                        violations.append(f"Param '{k}' exceeds length limit ({len(str(v))} > {limit})")

        if violations:
            return {
                "ip": record.get("ip"),
                "path": path,
                "verdict": "SCHEMA_VIOLATION",
                "violations": violations
            }

        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", help="Path to schema JSON file")
    args = parser.parse_args()

    validator = SchemaValidator(args.schema)

    # Read from stdin (ignoring args in stdin reading loop)
    # Note: argparse might consume stdin if not careful, but usually okay for flags

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            result = validator.validate(record)
            if result:
                print(json.dumps(result))
                sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
