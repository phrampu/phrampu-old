import paramiko
import yaml
import subprocess
import logging

LOGFILE = "server.log"
logging.basicConfig(filename=LOGFILE, filemode='w', format='%(asctime)s:%(levelname)s:%(message)s', datefmt='%m/%d/%Y %H:%M:%S', level=logging.DEBUG)

MACHINES = yaml.load(open('servers.yaml', 'r'))
client = paramiko.SSHClient()
client.load_system_host_keys()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def start_server(mach):
    current_directory = subprocess.getstatusoutput("pwd")
    subprocess.getstatusoutput(
        "ssh " + mach + " 'cd " + current_directory[1] +
        " && nohup python3 server.py &> /dev/null < /dev/null &'")

for cluster in MACHINES['clusters']:
    for machine in MACHINES['clusters'][cluster]['hostnames']:
        logging.info('initializing server on ', machine)
        start_server(machine)
