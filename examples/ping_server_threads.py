import http.server
import socketserver
import subprocess
import json
from urllib.parse import urlparse, parse_qs
import threading
from concurrent_coalesce import coalesce
import ipaddress

def is_valid_ip(ip_str: str) -> bool:
    """Validate if the string is a valid IP address."""
    try:
        ipaddress.ip_address(ip_str)
        return True
    except ValueError:
        return False

@coalesce()
def ping_host(host: str) -> dict:
    """Execute ping command for the given host and return results."""
    print("Collecting data for host: ", host)
    
    # -n 4 for Windows (4 packets), -c 4 for Unix-like systems
    ping_cmd = ['ping', '-n', '4', host] if subprocess.sys.platform == 'win32' else ['ping', '-c', '4', host]
    result = subprocess.run(ping_cmd, capture_output=True, text=True)
    
    return {
        'host': host,
        'success': result.returncode == 0,
        'output': result.stdout,
        'error': result.stderr if result.stderr else None
    }

class PingHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse the URL and query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        # Check if host parameter is provided
        if 'host' not in query_params:
            self.send_error(400, "Missing 'host' parameter")
            return
        
        host = query_params['host'][0]
        
        # Validate that host is an IP address
        if not is_valid_ip(host):
            self.send_error(400, "Host must be a valid IP address (IPv4 or IPv6)")
            return
        
        try:
            # Execute ping using coalesced function
            response = ping_host(host)

            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == "__main__":
    port = 8000
    with socketserver.ThreadingTCPServer(("", port), PingHandler) as httpd:
        print(f"Server running on port {port}")
        print("Try accessing: http://localhost:8000/?host=8.8.8.8")
        httpd.serve_forever()
