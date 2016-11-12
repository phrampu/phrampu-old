#!/usr/bin/python3
import threading
import paramiko, base64
import re
import subprocess
import csv
import os
import yaml
import datetime
from json import dumps, loads, JSONEncoder, JSONDecoder
from http.server import BaseHTTPRequestHandler,HTTPServer
from socketserver import ThreadingMixIn
import time
from pymongo import MongoClient
import logging
import logging.config
import filters
import argparse
import sys
from flask import Flask, json, Response

PORT = 57888
LDBPATH = "/p/lname/lname.db"
THREADS = 4
PASSWORD = os.environ.get('PHRAMPU_PASS')
USERNAME = os.environ.get('PHRAMPU_USER')
MACHINES = yaml.load(open('servers.yaml', 'r'))

def configurelogging():
    with open('filters.yaml', 'r') as the_file:
        config_dict = yaml.load(the_file)

    logging.config.dictConfig(config_dict)
configurelogging()

logger = logging.getLogger()

def getargs():
    parser = argparse.ArgumentParser(description='Initial settings for the server')
    parser.add_argument('-d', '--debug', nargs='?', choices=['DEBUG','INFO','WARNING','ERROR','CRITICAL'],
            help='the default debug level for logging')
    parser.add_argument('-v', '--verbose', help='Also output logging information to the console', action='store_true')

    args = parser.parse_args()

    if args.verbose:
        ch = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s:%(levelname)-7s:%(message)s', '[%m/%d/%Y %H:%M:%S]')
        ch.setFormatter(formatter)
        ch.addFilter(filters.MyFilter())
        logger.addHandler(ch)

    if args.debug is not None:
        logger.setLevel(args.debug)

getargs()

def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]

lnameDict = {}
connections = {}
whoCache = {}
hostnames = []
hostnameToCluster = {}
for cluster in MACHINES['clusters']:
    for hostname in MACHINES['clusters'][cluster]['hostnames']:
        hostnames.append(hostname)
        hostnameToCluster[hostname] = cluster
        if cluster not in whoCache:
            whoCache[cluster] = {}
hostnamesChunked = list(chunks(hostnames, len(hostnames)//THREADS))
threads = []
clients = []
mongo = MongoClient('mongodb://austinschwartz.com:27017/')
mongodb = mongo.phrampu
mongologs = mongodb.logs

# clears db if needed
# mongologs.drop()

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

def sshAndGetWho(i, hostname):
    logging.info('sshing into %s', hostname)
    who = []
    try:
        clients[i].connect(hostname, username=USERNAME, password=PASSWORD, look_for_keys=False)
        stdin, stdout, stderr = clients[i].exec_command('who')
        for line in stdout:
            who.append(line[:-2])
        clients[i].close()
    except Exception as e:
        logging.error(e)
        pass
    return who

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
        found = False
        for data in whoList:
            if data['lname']['careerAcc'] == careerAcc:
                data['devices'].append(device)
                found = True
        if not found:
            whoList.append({
                'lname': lnameDict[careerAcc],
                'timestamp': datetime.datetime.now().isoformat(),
                'devices': [device],
            })

    return whoList


def sshWorker(i, hostname):
    global whoCache
    cluster = hostnameToCluster[hostname]
    whoFormatted = formatWho(sshAndGetWho(i, hostname))
    whoCache[cluster][hostname] = whoFormatted
    for who in whoFormatted:
        mongologs.insert_one({
          'hostname': hostname,
          'cluster': cluster,
          'devices': who['devices'],
          'timestamp': who['timestamp'],
          'name': who['lname']['name'],
          'email': who['lname']['email'],
          'careerAcc': who['lname']['careerAcc'],
        }).inserted_id
    #pprint.pprint(whoCache)

def slaveDriverThread(i):
    while True:
        for hostname in hostnamesChunked[i]:
            logging.info('thread %s sshing to %s', i, hostname)
            sshWorker(i, hostname)
            time.sleep(5)
    return

app = Flask(__name__)

@app.route("/api/master")
def api_master():
    js = json.dumps({'response': whoCache})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/cluster/<cluster_name>")
def api_cluster():
    js = json.dumps({'response': whoCache[cluster_name]})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

if __name__ == "__main__":
    app.run(port=PORT)

#
#for i in range(THREADS):
#    t = threading.Thread(target=slaveDriverThread, args=(i,), daemon=True)
#    client = paramiko.SSHClient()
#    client.load_system_host_keys()
#    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
#    clients.append(client)
#    threads.append(t)
#    t.start()
#    time.sleep(1.5)
