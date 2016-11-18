import paramiko, base64
import settings as s
from collections import OrderedDict
import threading
import traceback
import util
import time
import re
import sys
from who import runWhoLocally, formatWho, lname, freeLabCount
from pymongo import MongoClient
from datetime import datetime, timedelta
from dateutil import tz
import dateutil.parser

lastTimeStamp = None

lnameDict = lname(s.LDBPATH)
connections = {}
whoCache = {}
hostnames = []
hostnameToCluster = {}
for cluster in s.MACHINES['clusters']:
    if cluster not in whoCache:
        whoCache[cluster] = OrderedDict()
    for hostname in s.MACHINES['clusters'][cluster]['hostnames']:
        hostnames.append(hostname)
        hostnameToCluster[hostname] = cluster

hostnamesChunked = list(util.chunks(hostnames, len(hostnames)//s.THREADS))
threads = []
clients = []
thread_times = []
mongo = MongoClient(s.MONGODB)
mongodb = mongo.phrampu
mongologs = mongodb.logs
mongocounts = mongodb.counts

def sshAndGetWho(client, hostname):
    s.log('sshing into %s', hostname)
    who = []
    try:
        client.connect(
            hostname,
            username=s.USERNAME,
            password=s.PASSWORD,
        )
        stdin, stdout, stderr = client.exec_command('w')
        # get rid of first two lines of w output
        stdout.readline()
        stdout.readline()
        for line in stdout:
            who.append(line)
        client.close()
    except Exception as e:
        s.logerror(e)
        pass
    return who

def sshWorker(i, hostname):
    global whoCache
    global lastTimeStamp
    cluster = hostnameToCluster[hostname]
    whoFormatted = formatWho(sshAndGetWho(clients[i], hostname), lnameDict)
    whoCache[cluster][hostname] = whoFormatted
    currentTime = datetime.now()
    thread_times[i] = currentTime
    if s.LOG_TO_MONGO:
        if i == 1:
            if lastTimeStamp is None:
                lastTimeStamp = currentTime
            else:
                tenMinsFromNow = currentTime + timedelta(minutes=10)
                if lastTimeStamp < tenMinsFromNow:
                    mongocounts.insert_one({
                      'timestamp': currentTime,
                      'counts': freeLabCount(whoCache)
                    }).inserted_id
                lastTimeStamp = currentTime
        for who in whoFormatted:
            mongologs.insert_one({
                'hostname': hostname,
                'cluster': cluster,
                'devices': who['devices'],
                'timestamp': who['timestamp'],
                'name': who['lname']['name'] if who['lname'] != 'None' else 'None',
                'email': who['lname']['email'] if who['lname'] != 'None' else 'None',
                'careerAcc': who['lname']['careerAcc'] if who['lname'] != 'None' else 'None',
              }).inserted_id


def slaveDriverThread(i):
    while True:
        for hostname in hostnamesChunked[i]:
            s.log('thread %s sshing to %s', i, hostname)
            try:
                sshWorker(i, hostname)
            except:
                e_type, e_value, e_traceback = sys.exc_info()
                s.log('thread %s broke while connecting to %s: %s', i, hostname, e_value)
                s.log('stack trace: %s', traceback.format_exc().splitlines())
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
        thread_times.append(datetime.now)
        t.start()
        time.sleep(1.5)

def formatTime(isotime):
    est = dateutil.parser.parse(isotime)
    t1 = est.replace(tzinfo=None) + timedelta(minutes=4)
    t2 = datetime.now().replace(tzinfo=None)
    if t1 > t2:
        return 'Current'
    else:
        return est.strftime('%Y-%m-%d %H:%M')

def lastFound(careerAcc):
    cursor = mongologs.find({'careerAcc': careerAcc}).sort([('timestamp', -1)])
    result = {}
    for logData in cursor:
        if 'tty7' in logData['devices']:
            result['careerAcc'] = careerAcc
            result['hostname'] = logData['hostname']
            result['cluster'] = logData['cluster']
            result['name'] = logData['name']
            result['timestamp'] = logData['timestamp']
            result['timeFormatted'] = formatTime(logData['timestamp'])
            break
    return result

def anyMatch(pattern, name):
    for n in name.split(' '):
        if pattern.match(n):
            return True
    return False

def find(regex):
    if len(regex) < 5:
        return {}
    pattern = re.compile(regex[1:-1].lower())
    users = set()
    ret = []
    for thing in lnameDict:
        if pattern.match(thing.lower()) or pattern.match(lnameDict[thing]['name'].lower()) or anyMatch(pattern, lnameDict[thing]['name'].lower()):
            users.add(thing)
    for user in users:
        f = lastFound(user)
        if f != {}:
            ret.append(f)
    return ret
