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
        "xinu00.cs.purdue.edu",
        "xinu01.cs.purdue.edu",
        "xinu02.cs.purdue.edu",
        "xinu03.cs.purdue.edu",
        "xinu04.cs.purdue.edu",
        "xinu05.cs.purdue.edu",
        "xinu06.cs.purdue.edu",
        "xinu07.cs.purdue.edu",
        "xinu08.cs.purdue.edu",
        "xinu09.cs.purdue.edu",
        "xinu10.cs.purdue.edu",
        "xinu11.cs.purdue.edu",
        "xinu12.cs.purdue.edu",
        "xinu13.cs.purdue.edu",
        "xinu14.cs.purdue.edu",
        "xinu15.cs.purdue.edu",
        "xinu16.cs.purdue.edu",
        "xinu17.cs.purdue.edu",
        "xinu18.cs.purdue.edu",
        "xinu19.cs.purdue.edu",
        "xinu20.cs.purdue.edu",
        "xinu21.cs.purdue.edu",
    ],
    "borg": [
        "borg00.cs.purdue.edu",
        "borg01.cs.purdue.edu",
        "borg02.cs.purdue.edu",
        "borg03.cs.purdue.edu",
        "borg04.cs.purdue.edu",
        "borg05.cs.purdue.edu",
        "borg06.cs.purdue.edu",
        "borg07.cs.purdue.edu",
        "borg08.cs.purdue.edu",
        "borg09.cs.purdue.edu",
        "borg10.cs.purdue.edu",
        "borg11.cs.purdue.edu",
        "borg12.cs.purdue.edu",
        "borg13.cs.purdue.edu",
        "borg14.cs.purdue.edu",
        "borg15.cs.purdue.edu",
        "borg16.cs.purdue.edu",
        "borg17.cs.purdue.edu",
        "borg18.cs.purdue.edu",
        "borg19.cs.purdue.edu",
        "borg20.cs.purdue.edu",
        "borg21.cs.purdue.edu",
        "borg22.cs.purdue.edu",
        "borg23.cs.purdue.edu",
        "borg24.cs.purdue.edu",
    ],
    "sslab": [
        "sslab00.cs.purdue.edu",
        "sslab01.cs.purdue.edu",
        "sslab02.cs.purdue.edu",
        "sslab03.cs.purdue.edu",
        "sslab04.cs.purdue.edu",
        "sslab05.cs.purdue.edu",
        "sslab06.cs.purdue.edu",
        "sslab07.cs.purdue.edu",
        "sslab08.cs.purdue.edu",
        "sslab09.cs.purdue.edu",
        "sslab10.cs.purdue.edu",
        "sslab11.cs.purdue.edu",
        "sslab12.cs.purdue.edu",
        "sslab13.cs.purdue.edu",
        "sslab14.cs.purdue.edu",
        "sslab15.cs.purdue.edu",
        "sslab16.cs.purdue.edu",
        "sslab17.cs.purdue.edu",
        "sslab18.cs.purdue.edu",
        "sslab19.cs.purdue.edu",
        "sslab20.cs.purdue.edu",
        "sslab21.cs.purdue.edu",
        "sslab22.cs.purdue.edu",
        "sslab23.cs.purdue.edu",
        "sslab24.cs.purdue.edu",
    ],
    "moore": [
        "moore00.cs.purdue.edu",
        "moore01.cs.purdue.edu",
        "moore02.cs.purdue.edu",
        "moore03.cs.purdue.edu",
        "moore04.cs.purdue.edu",
        "moore05.cs.purdue.edu",
        "moore06.cs.purdue.edu",
        "moore07.cs.purdue.edu",
        "moore08.cs.purdue.edu",
        "moore09.cs.purdue.edu",
        "moore10.cs.purdue.edu",
        "moore11.cs.purdue.edu",
        "moore12.cs.purdue.edu",
        "moore13.cs.purdue.edu",
        "moore14.cs.purdue.edu",
        "moore15.cs.purdue.edu",
        "moore16.cs.purdue.edu",
        "moore17.cs.purdue.edu",
        "moore18.cs.purdue.edu",
        "moore19.cs.purdue.edu",
        "moore20.cs.purdue.edu",
        "moore21.cs.purdue.edu",
        "moore22.cs.purdue.edu",
        "moore23.cs.purdue.edu",
        "moore24.cs.purdue.edu",
    ],
    "escher": [
        "escher00.cs.purdue.edu",
        "escher01.cs.purdue.edu",
        "escher02.cs.purdue.edu",
        "escher03.cs.purdue.edu",
        "escher04.cs.purdue.edu",
        "escher05.cs.purdue.edu",
        "escher06.cs.purdue.edu",
        "escher07.cs.purdue.edu",
        "escher08.cs.purdue.edu",
        "escher09.cs.purdue.edu",
        "escher10.cs.purdue.edu",
        "escher11.cs.purdue.edu",
        "escher12.cs.purdue.edu",
        "escher13.cs.purdue.edu",
        "escher14.cs.purdue.edu",
        "escher15.cs.purdue.edu",
        "escher16.cs.purdue.edu",
        "escher17.cs.purdue.edu",
        "escher18.cs.purdue.edu",
        "escher19.cs.purdue.edu",
        "escher20.cs.purdue.edu",
        "escher21.cs.purdue.edu",
        "escher22.cs.purdue.edu",
        "escher23.cs.purdue.edu",
        "escher24.cs.purdue.edu",
    ],
    "pod": [
        "pod0-0.cs.purdue.edu",
        "pod1-1.cs.purdue.edu",
        "pod1-2.cs.purdue.edu",
        "pod1-3.cs.purdue.edu",
        "pod1-4.cs.purdue.edu",
        "pod1-5.cs.purdue.edu",
        "pod2-1.cs.purdue.edu",
        "pod2-2.cs.purdue.edu",
        "pod2-3.cs.purdue.edu",
        "pod2-4.cs.purdue.edu",
        "pod2-5.cs.purdue.edu",
        "pod3-1.cs.purdue.edu",
        "pod3-2.cs.purdue.edu",
        "pod3-3.cs.purdue.edu",
        "pod3-4.cs.purdue.edu",
        "pod3-5.cs.purdue.edu",
        "pod4-1.cs.purdue.edu",
        "pod4-2.cs.purdue.edu",
        "pod4-3.cs.purdue.edu",
        "pod4-4.cs.purdue.edu",
        "pod4-5.cs.purdue.edu",
        "pod5-1.cs.purdue.edu",
        "pod5-2.cs.purdue.edu",
        "pod5-3.cs.purdue.edu",
        "pod5-4.cs.purdue.edu",
        "pod5-5.cs.purdue.edu",
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
    
