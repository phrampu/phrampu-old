import paramiko, base64
import settings as s
from collections import OrderedDict
import threading
import util
import time
from who import runWhoLocally, formatWho, lname
from pymongo import MongoClient

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

def sshAndGetWho(client, hostname):
    s.log('sshing into %s', hostname)
    who = []
    try:
        client.connect(
            hostname, 
            username=s.USERNAME, 
            password=s.PASSWORD, 
            look_for_keys=False
        )
        stdin, stdout, stderr = client.exec_command('who')
        for line in stdout:
            who.append(line[:-2])
        client.close()
    except Exception as e:
        s.logerror(e)
        pass
    return who

def sshWorker(i, hostname):
    global whoCache
    cluster = hostnameToCluster[hostname]
    whoFormatted = formatWho(sshAndGetWho(clients[i], hostname), lnameDict)
    whoCache[cluster][hostname] = whoFormatted
    if s.LOG_TO_MONGO:
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

def formatTime(isotime):
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()
    utc = dateutil.parser.parse(isotime)
    utc = utc.replace(tzinfo=from_zone)
    est = utc.astimezone(to_zone)
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
            result['hostname'] = logData['hostname']
            result['timestamp'] = logData['timestamp']
            break
    return result
