#!/usr/bin/env python3
"""
request_entropy_analyzer.py
Layer 7 Anti-DDoS Script: Entropy analysis for URLs and Payloads.

Purpose:
Detects DGA (Domain Generation Algorithm) style attacks or randomized query parameters
often used by bots to bypass caches (Cache Busting) or in SQL Injection fuzzing.

Logic:
Calculates Shannon Entropy of specific fields. High entropy suggests randomness (encrypted data,
hashes, random strings). Very low entropy might indicate repetitive attacks.

Usage:
    python3 request_entropy_analyzer.py < log_stream.json
"""

import sys
import json
import math
from urllib.parse import urlparse, parse_qs

# Configuration
HIGH_ENTROPY_THRESHOLD = 4.5  # Threshold for random-looking strings
MAX_PARAM_LENGTH_CHECK = 100  # Only check longer parameters for efficiency

def calculate_shannon_entropy(data):
    """Calculates the Shannon entropy of a string."""
    if not data:
        return 0
    entropy = 0
    length = len(data)

    # Count frequencies
    frequencies = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1

    # Calculate entropy
    for char in frequencies:
        p_x = frequencies[char] / length
        entropy += - p_x * math.log2(p_x)

    return entropy

def analyze_request(record):
    url = record.get("url", "")
    method = record.get("method", "")
    body = record.get("body", "") # Assuming body might be captured in some logs

    parsed = urlparse(url)
    path = parsed.path
    query_params = parse_qs(parsed.query)

    anomalies = []

    # 1. Analyze Path Segments
    # Detecting randomized path segments like /api/v1/user/a8f9e7b2...
    segments = path.strip('/').split('/')
    for segment in segments:
        e = calculate_shannon_entropy(segment)
        if e > HIGH_ENTROPY_THRESHOLD and len(segment) > 8:
            anomalies.append(f"High entropy path segment: {segment} ({e:.2f})")

    # 2. Analyze Query Parameters
    # Detecting cache busting: ?nonce=384759283745...
    for key, values in query_params.items():
        for val in values:
            if len(val) > 8:
                e = calculate_shannon_entropy(val)
                if e > HIGH_ENTROPY_THRESHOLD:
                    anomalies.append(f"High entropy param '{key}': {val[:10]}... ({e:.2f})")

    # 3. Analyze Body (if present)
    if body and len(body) < 2048: # Limit analysis size
        e = calculate_shannon_entropy(body)
        if e > 5.5: # Higher threshold for body which might be binary/compressed
            anomalies.append(f"High entropy body ({e:.2f})")

    score = len(anomalies) * 20

    return {
        "ip": record.get("ip"),
        "url": url,
        "entropy_score": score,
        "anomalies": anomalies,
        "verdict": "SUSPICIOUS" if score > 0 else "CLEAN"
    }

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
            result = analyze_request(record)
            print(json.dumps(result))
            sys.stdout.flush()
        except json.JSONDecodeError:
            pass
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
