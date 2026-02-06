import unittest
import socket
import time
import sys
import os

# Add the directory to sys.path so we can import the module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from soc_dashboard_backend import SOCDashboardBackend

class TestSOCDashboardSecurity(unittest.TestCase):
    def test_bind_address(self):
        # Use port 0 to let OS assign a free port
        backend = SOCDashboardBackend(port=0)
        backend.start()
        try:
            # Get the actual address and port
            host, port = backend.server.server_address
            print(f"Server bound to: {host}:{port}")

            # Assert that the host is explicitly localhost
            # Note: TCPServer bound to "" typically reports '0.0.0.0'
            # We want it to be '127.0.0.1'
            self.assertEqual(host, "127.0.0.1", "Server should bind to localhost (127.0.0.1) only, not 0.0.0.0")

        finally:
            backend.stop()

if __name__ == "__main__":
    unittest.main()
