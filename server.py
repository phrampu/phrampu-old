#!/usr/bin/python3

import pprint
import paramiko, base64
import re
import subprocess
import csv
from json import dumps, loads, JSONEncoder, JSONDecoder
from http.server import BaseHTTPRequestHandler,HTTPServer

PORT = 57888
LDBPATH = "/p/lname/lname.db"
MACHINES = {
    "xinu": [
        "xinu01.cs.purdue.edu",
        "xinu02.cs.purdue.edu",
        "xinu03.cs.purdue.edu",
        "xinu04.cs.purdue.edu",
        "xinu05.cs.purdue.edu",
        "xinu06.cs.purdue.edu",
        "xinu07.cs.purdue.edu",
    ],
    "borg": [
        "borg01.cs.purdue.edu",
    ],
    "sslab": [
        "sslab00.cs.purdue.edu",
        "sslab01.cs.purdue.edu",
        "sslab02.cs.purdue.edu",
        "sslab03.cs.purdue.edu",
        "sslab04.cs.purdue.edu",
        "sslab05.cs.purdue.edu",
        "sslab06.cs.purdue.edu",
    ],
    "data": [
        "data.cs.purdue.edu",
    ],
    "lore": [
        "lore.cs.purdue,edu",
    ],
}
PASSWORD = '???'
USERNAME = '???'

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

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

def runWho():
    # Run + split who on new lines
    return subprocess.check_output("who").decode().split('\n')

def formatWho(who):
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

#@lru_cache(maxsize=16)
def sshAndGetWho(hostname):
    print("sshing into ", hostname)
    who = []
    try:
        client.connect(hostname, username=USERNAME, password=PASSWORD, look_for_keys=False)
        stdin, stdout, stderr = client.exec_command('who')
        for line in stdout:
            who.append(line[:-2])
        client.close()
    except:
        pass
    return who


#pp = pprint.PrettyPrinter(indent=4)
#pp.pprint(lnameDict)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if None != re.search('/who', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            self.wfile.write(dumps({'response': formatWho(runWho())}).encode())
        elif None != re.search('/master', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            response = {}
            for cluster in MACHINES:
                response[cluster] = {}
                for machine in MACHINES[cluster]:
                    response[cluster][machine] = formatWho(sshAndGetWho(machine))
            self.wfile.write(dumps({'response': response}).encode())
        elif None != re.search('/find', self.path):
            user = self.path[self.path.find('find') + 5:]
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            response = {}
            response['user'] = {}
            response['machines'] = {}
            for cluster in MACHINES:
                for machine in MACHINES[cluster]:
                    dic = formatWho(sshAndGetWho(machine))
                    for userDict in dic:
                        if userDict['careerAcc'] == user:
                            response['user'] = userDict
                            response['machines'][cluster] = machine
            
            self.wfile.write(dumps({'response': response}).encode())
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
    
