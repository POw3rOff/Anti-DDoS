
import time
import hashlib
import hmac
import base64
import os
import secrets
import logging

class JSChallenge:
    """
    Layer 7: Javascript Challenge (Anti-Bot).
    Generates an HTML page that forces the client to solve a math puzzle
    and reload with a valid token.
    """
    def __init__(self, secret_key=None):
        self.secret_key = secret_key or os.getenv("UAD_JS_SECRET")
        if not self.secret_key:
            logging.warning("JSChallenge: No secret key provided. Using ephemeral random key.")
            self.secret_key = secrets.token_hex(32)

    def _create_token(self, client_ip, timestamp=None):
        """Creates a signed token for the given IP and timestamp."""
        if timestamp is None:
            timestamp = int(time.time())

        # Message to sign
        message = f"{client_ip}:{timestamp}"

        # Compute HMAC
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        # Combine timestamp and signature
        token_data = f"{timestamp}:{signature}"

        # Base64 encode for cookie safety
        return base64.urlsafe_b64encode(token_data.encode()).decode()

    def generate_challenge(self, client_ip):
        """Returns the HTML content for the interstitial page."""
        token = self._create_token(client_ip)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>DDoS Protection</title>
            <script>
                // Simple calculation to prove CPU time
                function solve() {{
                    var token = "{token}";
                    var solution = 0;
                    for(var i=0; i<5000; i++) {{
                        solution += Math.sqrt(i);
                    }}
                    document.cookie = "uad_token=" + token + "; path=/; max-age=3600";
                    window.location.reload();
                }}
                setTimeout(solve, 500);
            </script>
        </head>
        <body>
            <h1>Checking your browser...</h1>
            <p>Please wait while we verify your request.</p>
        </body>
        </html>
        """
        return html

    def validate_token(self, client_ip, token):
        """Validates the returned token cookie."""
        try:
            # Decode token
            if not token:
                return False
            token_data = base64.urlsafe_b64decode(token).decode()
            parts = token_data.split(":")
            if len(parts) != 2:
                return False

            timestamp_str, received_signature = parts
            timestamp = int(timestamp_str)

            # Check timestamp window (5 minutes)
            now = time.time()
            if abs(now - timestamp) > 300:
                return False

            # Recompute signature
            message = f"{client_ip}:{timestamp}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()

            # Verify signature securely
            return hmac.compare_digest(received_signature, expected_signature)

        except Exception:
            # Catch all: decoding errors, int conversion errors, etc.
            return False
