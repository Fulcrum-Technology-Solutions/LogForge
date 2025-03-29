#\!/usr/bin/env python3
"""
Simple HTTP server for testing Logforge HTTP output.
This server listens on port 8080 and logs any incoming HTTP requests.
"""

import http.server
import socketserver
import json
import logging
import os
import datetime

# Configure logging
log_dir = "server_logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "http_server.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Port to listen on
PORT = 8080

class LogHandler(http.server.BaseHTTPRequestHandler):
    """Handler that logs the request content and responds with 200 OK."""
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get('Content-Length', 0))
        content = self.rfile.read(content_length)
        
        # Try to decode as JSON for nicer logging
        try:
            data = json.loads(content)
            content_str = json.dumps(data, indent=2)
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON, just use the raw content
            content_str = str(content)
            
        # Log the request details
        logging.info(f"Received request to {self.path}")
        logging.info(f"Headers: {dict(self.headers)}")
        logging.info(f"Content: {content_str[:500]}...")
        
        # Save the log to a file based on the data type (if recognizable)
        if self.path == "/api/logs":
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            extension = ".log"
            
            # Try to determine file extension
            content_type = self.headers.get('Content-Type', '').lower()
            if content_type == 'application/json':
                extension = ".json"
            elif content_type.startswith('application/xml') or content_type.startswith('text/xml'):
                extension = ".xml"
                
            # Create a log file for each received request
            log_file = os.path.join(log_dir, f"received_{timestamp}{extension}")
            with open(log_file, 'wb') as f:
                f.write(content)
            logging.info(f"Saved content to {log_file}")
        
        # Send response
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        # Send a JSON response
        response = {
            "status": "success",
            "message": "Log received",
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.wfile.write(json.dumps(response).encode('utf-8'))
        
    def do_GET(self):
        """Handle GET requests with a simple status page."""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        
        response = f"""<html>
        <head><title>Logforge Test Server</title></head>
        <body>
            <h1>Logforge Test Server</h1>
            <p>This server is running and ready to receive logs at POST /api/logs</p>
            <p>Received logs are saved in the {log_dir} directory.</p>
            <p>Current time: {datetime.datetime.now().isoformat()}</p>
        </body>
        </html>
        """
        self.wfile.write(response.encode('utf-8'))

def run_server():
    """Run the HTTP server."""
    with socketserver.TCPServer(("", PORT), LogHandler) as httpd:
        logging.info(f"Server started at http://localhost:{PORT}")
        logging.info(f"Send logs to http://localhost:{PORT}/api/logs")
        logging.info(f"Logs will be saved to the {log_dir} directory")
        logging.info("Press Ctrl+C to stop the server")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Server stopped")

if __name__ == "__main__":
    run_server()
