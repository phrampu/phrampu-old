#!/usr/bin/python3

import re
import subprocess
from json import dumps, loads, JSONEncoder, JSONDecoder
from http.server import BaseHTTPRequestHandler,HTTPServer

PORT = 57888

def getWho():
    # Split who on new lines
    who = subprocess.check_output("who").decode().split('\n')

    # Get first column
    who = [line.split(' ')[0] for line in who]

    # Remove empty strings
    who = filter(None, who)

    return list(set(who))

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if None != re.search('/who', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            self.wfile.write(dumps(
                {'response': getWho()}).encode()
            )
        else:
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()

try:
    server = HTTPServer(('', PORT), handler)
    print('STARTING ON ' , PORT)
    
    server.serve_forever()

except KeyboardInterrupt:
    print('SHUTTING DOWN')
    server.socket.close()
    
