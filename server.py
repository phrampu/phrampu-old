#!/usr/bin/python3

from http.server import BaseHTTPRequestHandler,HTTPServer

PORT = 57888

class handler(BaseHTTPRequestHandler):
    def get(self):
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.wfile.write(b'Hello World!')
        return

try:
    server = HTTPServer(('', PORT), handler)
    print('STARTING ON ' , PORT)
    
    server.serve_forever()

except KeyboardInterrupt:
    print('SHUTTING DOWN')
    server.socket.close()
    
