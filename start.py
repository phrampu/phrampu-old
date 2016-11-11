import paramiko
import yaml
import subprocess

MACHINES = yaml.load(open('servers.yaml', 'r'))
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

for cluster in MACHINES['clusters']:
    for machine in MACHINES['clusters'][cluster]['hostnames']:
        print('initializing server on ', machine)
        current_directory=subprocess.getstatusoutput("pwd")
        subprocess.getstatusoutput(
            "ssh sslab00 'cd " + current_directory[1] +
            " && nohup python3 server.py &> /dev/null < /dev/null &'")