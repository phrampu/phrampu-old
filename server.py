#!/usr/bin/python3

import pprint
import re
import subprocess
import csv
from json import dumps, loads, JSONEncoder, JSONDecoder
from http.server import BaseHTTPRequestHandler,HTTPServer

PORT = 57888
LDBPATH = "/p/lname/lname.db"

lnameDict = {}

def lname():
    with open(LDBPATH, 'r') as ldb:
        ldbreader = csv.reader(ldb, delimiter=':', quotechar='|')
        for row in ldbreader:
            firstComma = row[1].find(',')
            lnameDict[row[0]] = {
                "careerAcc": row[0],
                "name": row[1][:firstComma],
                "email": row[2],
            }
lname()

#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(lnameDict)

def getWho():
    # Split who on new lines
    who = subprocess.check_output("who").decode().split('\n')

    # Get first column
    who = [line.split(' ')[0] for line in who]

    # Remove empty strings
    who = filter(None, who)

    # Remove duplicates
    who = list(set(who))

    whoList = []
    for person in who:
        whoList.append(lnameDict[person])

    return whoList

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if None != re.search('/who', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            self.wfile.write(dumps({'response': getWho()}).encode())
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
    
