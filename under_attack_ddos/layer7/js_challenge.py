
import time
import hashlib
import hmac
import os
import secrets
import base64

class JSChallenge:
    """
    Layer 7: Javascript Challenge (Anti-Bot).
    Generates an HTML page that forces the client to solve a math puzzle
    and reload with a valid token.
    """
    def __init__(self, secret_key=None):
        # Use provided key, or environment variable, or generate a secure random one
        self.secret_key = secret_key or os.getenv("UAD_JS_SECRET")
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            # In production, this means tokens are invalid after restart, which is secure.

    def _generate_signature(self, client_ip, timestamp):
        """Generates an HMAC signature for the given IP and timestamp."""
        message = f"{client_ip}:{timestamp}".encode()
        return hmac.new(self.secret_key.encode(), message, hashlib.sha256).hexdigest()

    def generate_challenge(self, client_ip):
        """Returns the HTML content for the interstitial page."""
        timestamp = int(time.time())
        signature = self._generate_signature(client_ip, timestamp)
        # Token format: timestamp:signature
        token_raw = f"{timestamp}:{signature}"
        token = base64.urlsafe_b64encode(token_raw.encode()).decode()
        
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
            # Token is base64(timestamp:signature)
            decoded = base64.urlsafe_b64decode(token).decode()
            timestamp_str, signature = decoded.split(":")
            timestamp = int(timestamp_str)

            # Check if timestamp is within valid window (e.g., 5 minutes)
            now = time.time()
            if abs(now - timestamp) > 300:
                return False

            expected_signature = self._generate_signature(client_ip, timestamp)
            return hmac.compare_digest(signature, expected_signature)
        except (ValueError, IndexError, AttributeError):
            return False
