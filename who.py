import csv
import subprocess
import datetime

def lname(path):
    lnameDict = {}
    with open(path, 'r') as ldb:
        ldbreader = csv.reader(ldb, delimiter=':', quotechar='|')
        for row in ldbreader:
            firstComma = row[1].find(',')
            lnameDict[row[0]] = {
                "careerAcc": row[0],
                "name": row[1][:firstComma],
                "email": row[2],
            }
    return lnameDict

def runWhoLocally():
    # Run + split who on new lines
    return subprocess.check_output("who").decode().split('\n')

def formatWho(who, lnameDict):
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
                'lname': lnameDict[careerAcc] if careerAcc in lnameDict else 'None',
                'timestamp': datetime.datetime.now().isoformat(),
                'devices': [device],
            })

    return whoList

def freeLabCount(whoData):
    ret = {}
    for cluster, hosts in whoData.items():
        if cluster not in ret:
            ret[cluster] = {
                'taken': 0,
                'free': len(hosts),
                'total': len(hosts)
            }
        for host, hostData in hosts.items():
            for person in hostData:
                for device in person['devices']:
                    if device.startswith('tty'):
                        if cluster in ret:
                            ret[cluster]['taken'] += 1
                            ret[cluster]['free'] -= 1
                        else:
                            ret[cluster] = {
                                'taken': 1,
                                'free': len(hosts) - 1,
                                'total': len(hosts)
                            }
    return ret
