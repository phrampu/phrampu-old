#!/usr/bin/python3

import pprint
import paramiko, base64
import re
import subprocess
import csv
import os
import requests
import zerorpc
import yaml
from json import dumps, loads, JSONEncoder, JSONDecoder
from http.server import BaseHTTPRequestHandler,HTTPServer

PORT = 57888
LDBPATH = "/p/lname/lname.db"
PASSWORD = os.environ.get('PHRAMPU_PASS')
USERNAME = os.environ.get('PHRAMPU_USER')
MACHINES = yaml.load(open('servers.yaml', 'r'))

client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

lnameDict = {}
connections = {}

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

def runWhoLocally():
    # Run + split who on new lines
    return subprocess.check_output("who").decode().split('\n')

def formatWho(who):
    who = list(filter(None, who))

    # First col (username)
    whoCol1 = [line.split()[0] for line in who]

    # Second col (tty/pts)
    whoCol2 = [line.split()[1] for line in who]

    whoZip = list(zip(whoCol1, whoCol2))

    whoList = []
    for (careerAcc, device) in whoZip:
        whoList.append({
            'careerAcc': careerAcc,
            'device': device,
        })

    return whoList

def getAlive(hostname):
    req = None
    try:
        req = requests.get('http://' + hostname + ':' + str(PORT) + '/check')
        if req:
            return True
    except:
        pass
    return False

def getWho(hostname):
    req = None
    try:
        req = requests.get('http://' + hostname + ':' + str(PORT) + '/who')
        if req:
            return req.json()
    except:
        pass
    return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if None != re.search('/who', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            self.wfile.write(dumps({'response': formatWho(runWhoLocally())}).encode())

        ### deprecated ###
        elif None != re.search('/master', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            self.wfile.write(dumps({'response': 'deprecated'}).encode())

        elif None != re.search('/find', self.path):
            user = self.path[self.path.find('find') + 5:]
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()

            self.wfile.write(dumps({'response': 'deprecated'}).encode())
        #####

        elif None != re.search('/check', self.path):
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            self.wfile.write(dumps({'alive': 'yes'}).encode())

        elif None != re.search('/api/cluster', self.path):
            cluster = self.path[self.path.find('cluster') + 8:]
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            response = {}
            if cluster in MACHINES:
                response[cluster] = []
                for machine in MACHINES[cluster]:
                    who = getWho(machine)
                    response[cluster].append({
                        'hostname': machine,
                        'alive': 'yes' if who != None else 'no',
                        'response': who['response'] if who != None else {}
                    })
                
            self.wfile.write(dumps({'response': response}).encode())
        elif None != re.search('/api/host/', self.path):
            host = self.path[self.path.find('host') + 5:]
            self.send_response(200)
            self.send_header('Content-type','application/json')
            self.end_headers()
            response = getWho(host)
            if response == None:
                response = {'response': 'not alive'}
            
            self.wfile.write(dumps({'response': response['response']}).encode())
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
