#!/usr/bin/env python3
"""
challenge_response_middleware.py
Layer 7 Anti-DDoS Script: Manages progressive challenges (JS, Token, PoW).

Purpose:
Determines the appropriate challenge level for a client based on their reputation score.
Generates challenge payloads (simulated) and verifies responses.

Challenge Levels:
0. None (Pass)
1. Cookie Check (Silent)
2. JavaScript Calculation (Light)
3. Proof of Work (Heavy - SHA256 puzzle)
4. CAPTCHA (Interactive)
5. Block

Usage:
    Import as module or run to verify challenge logic.
"""

import hashlib
import time
import random
import string
import json
import sys

class ChallengeManager:
    def __init__(self):
        self.secrets = {} # ip -> current_challenge_solution

    def get_mitigation_action(self, ip, risk_score):
        """Decides action based on risk score (0-100)."""
        if risk_score < 20:
            return "PASS"
        elif risk_score < 40:
            return "JS_CHALLENGE"
        elif risk_score < 70:
            return "POW_CHALLENGE"
        elif risk_score < 90:
            return "CAPTCHA"
        else:
            return "BLOCK"

    def generate_pow_challenge(self, ip, difficulty=4):
        """Generates a Proof-of-Work challenge (find nonce where hash starts with N zeros)."""
        prefix = ''.join(random.choices(string.ascii_letters, k=8))
        target = "0" * difficulty

        challenge = {
            "type": "POW",
            "prefix": prefix,
            "difficulty": difficulty,
            "description": f"Find a suffix string S such that SHA256({prefix} + S) starts with {difficulty} zeros."
        }

        # Store for verification (stateless approach would use signed tokens)
        self.secrets[ip] = {"type": "POW", "prefix": prefix, "target": target}
        return challenge

    def verify_pow_response(self, ip, response):
        """Verifies the PoW solution provided by client."""
        if ip not in self.secrets:
            return False

        expected = self.secrets[ip]
        if expected["type"] != "POW":
            return False

        suffix = response.get("solution", "")
        prefix = expected["prefix"]
        target = expected["target"]

        # Verify hash
        candidate = f"{prefix}{suffix}"
        digest = hashlib.sha256(candidate.encode()).hexdigest()

        if digest.startswith(target):
            del self.secrets[ip] # Consume challenge
            return True
        return False

    def generate_js_challenge(self, ip):
        """Generates a simple arithmetic/logic challenge for JS."""
        a = random.randint(10, 99)
        b = random.randint(10, 99)
        op = random.choice(["+", "*"])

        code = f"var a={a}; var b={b}; return a{op}b;"
        expected = a * b if op == "*" else a + b

        self.secrets[ip] = {"type": "JS", "expected": str(expected)}

        return {
            "type": "JS",
            "code": code,
            "description": "Execute JS and send result."
        }

    def verify_js_response(self, ip, response):
        if ip not in self.secrets:
            return False

        expected = self.secrets[ip]
        if expected["type"] != "JS":
            return False

        result = str(response.get("solution", ""))
        if result == expected["expected"]:
            del self.secrets[ip]
            return True
        return False

# Self-test / CLI mode
def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        manager = ChallengeManager()
        ip = "1.2.3.4"

        # Test 1: JS Challenge
        print("[*] Testing JS Challenge...")
        chall = manager.generate_js_challenge(ip)
        print(f"Generated: {chall}")
        # Solve it (hacky eval for test)
        # In python we need to parse the code string.
        # code is "var a=X; var b=Y; return a*b;" -> extracted for test
        parts = chall["code"].split(';')
        a = int(parts[0].split('=')[1])
        b = int(parts[1].split('=')[1])
        op = "+" if "+" in parts[2] else "*"
        solution = a + b if op == "+" else a * b

        valid = manager.verify_js_response(ip, {"solution": solution})
        print(f"Verification: {valid}")

        # Test 2: PoW Challenge
        print("\n[*] Testing PoW Challenge...")
        chall = manager.generate_pow_challenge(ip, difficulty=3) # Low difficulty for fast test
        print(f"Generated: {chall}")

        # Brute force solution
        prefix = chall["prefix"]
        target = "0" * chall["difficulty"]
        nonce = 0
        while True:
            candidate = f"{prefix}{nonce}"
            h = hashlib.sha256(candidate.encode()).hexdigest()
            if h.startswith(target):
                print(f"Found solution: {nonce} -> {h}")
                break
            nonce += 1

        valid = manager.verify_pow_response(ip, {"solution": str(nonce)})
        print(f"Verification: {valid}")
    else:
        print("Run with --test to see internal logic test.")
        # Or standard input mode could be implemented to act as an external verifier service
        print("Standard mode expects JSON input: {'action': 'generate'|'verify', 'ip': '...', 'score': ...}")

        for line in sys.stdin:
            try:
                data = json.loads(line)
                manager = ChallengeManager() # State would be lost here in CLI mode per line,
                                          # typically this runs as a service or with persistent storage.
                                          # For demonstration, we just print what WOULD happen.

                if data.get("action") == "generate":
                    score = data.get("score", 0)
                    action = manager.get_mitigation_action(data.get("ip"), score)
                    print(json.dumps({"ip": data.get("ip"), "recommended_action": action}))
            except:
                pass

if __name__ == "__main__":
    main()
