#!/usr/bin/python3
from collections import OrderedDict
import threading
import paramiko, base64
import sys
import time
import util
from json import dumps, loads, JSONEncoder, JSONDecoder
from pymongo import MongoClient

from flask import Flask, json, Response
from flask_cors import CORS, cross_origin

from who import lname, runWhoLocally, formatWho
import settings as s

logger = s.logging.getLogger()
s.getargs(logger)

lnameDict = lname(s.LDBPATH)
connections = {}
whoCache = {}
hostnames = []
hostnameToCluster = {}
for cluster in s.MACHINES['clusters']:
    for hostname in s.MACHINES['clusters'][cluster]['hostnames']:
        hostnames.append(hostname)
        hostnameToCluster[hostname] = cluster
        if cluster not in whoCache:
            whoCache[cluster] = OrderedDict()

hostnamesChunked = list(util.chunks(hostnames, len(hostnames)//s.THREADS))
threads = []
clients = []
mongo = MongoClient(s.MONGODB)
mongodb = mongo.phrampu
mongologs = mongodb.logs

# clears db if needed
# mongologs.drop()

def sshAndGetWho(i, hostname):
    s.log('sshing into %s', hostname)
    who = []
    try:
        clients[i].connect(
            hostname, 
            username=s.USERNAME, 
            password=s.PASSWORD, 
            look_for_keys=False
        )
        stdin, stdout, stderr = clients[i].exec_command('who')
        for line in stdout:
            who.append(line[:-2])
        clients[i].close()
    except Exception as e:
        s.logerror(e)
        pass
    return who



def sshWorker(i, hostname):
    global whoCache
    cluster = hostnameToCluster[hostname]
    whoFormatted = formatWho(sshAndGetWho(i, hostname), lnameDict)
    whoCache[cluster][hostname] = whoFormatted
    #for who in whoFormatted:
        # mongologs.insert_one({
        #   'hostname': hostname,
        #   'cluster': cluster,
        #   'devices': who['devices'],
        #   'timestamp': who['timestamp'],
        #   'name': who['lname']['name'] if who['lname'] != 'None' else 'None',
        #   'email': who['lname']['email'] if who['lname'] != 'None' else 'None',
        #   'careerAcc': who['lname']['careerAcc'] if who['lname'] != 'None' else 'None',
        # }).inserted_id

def slaveDriverThread(i):
    while True:
        for hostname in hostnamesChunked[i]:
            s.log('thread %s sshing to %s', i, hostname)
            sshWorker(i, hostname)
            time.sleep(5)
    return

def spawnThreads():
    for i in range(s.THREADS):
        t = threading.Thread(target=slaveDriverThread, args=(i,), daemon=True)
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        clients.append(client)
        threads.append(t)
        t.start()
        time.sleep(1.5)

threading.Thread(target=spawnThreads, daemon=True).start()

app = Flask(__name__)
CORS(app)

@app.route("/api/master")
@cross_origin()
def api_master():
    js = json.dumps({'response': whoCache})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

@app.route("/api/cluster/<cluster_name>")
@cross_origin()
def api_cluster():
    js = json.dumps({'response': whoCache[cluster_name]})
    resp = Response(js, status=200, mimetype='application/json')
    return resp

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=s.PORT)
