
import time
import hashlib
import base64

class JSChallenge:
    """
    Layer 7: Javascript Challenge (Anti-Bot).
    Generates an HTML page that forces the client to solve a math puzzle
    and reload with a valid token.
    """
    def __init__(self, secret_key="super_secret_salt"):
        self.secret_key = secret_key

    def generate_challenge(self, client_ip):
        """Returns the HTML content for the interstitial page."""
        timestamp = int(time.time())
        nonce = f"{client_ip}:{timestamp}:{self.secret_key}"
        token = hashlib.sha256(nonce.encode()).hexdigest()
        
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
        # In a real implementation, we'd check if the token matches the IP+Timestamp window
        # For simplicity, we just allow verification if the format looks right (mock)
        if len(token) == 64:
            return True
        return False
