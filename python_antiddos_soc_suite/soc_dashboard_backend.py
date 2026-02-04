import http.server
import socketserver
import json
import threading
import time

class SOCDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # This would fetch real data from the master controller or shared store
            status = {
                'system_status': 'OPERATIONAL',
                'active_incidents': 0,
                'traffic_rps': 42,
                'blocked_ips_count': 15,
                'timestamp': time.time()
            }
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()

class SOCDashboardBackend:
    def __init__(self, port=8000):
        self.port = port
        self.server = None
        self.thread = None

    def start(self):
        handler = SOCDashboardHandler
        self.server = socketserver.TCPServer(("", self.port), handler)
        print(f"SOC Dashboard Backend serving at port {self.port}")
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()

if __name__ == "__main__":
    backend = SOCDashboardBackend(8080)
    backend.start()
    print("Running for 5 seconds...")
    time.sleep(5)
    backend.stop()