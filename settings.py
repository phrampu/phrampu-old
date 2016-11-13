import os
import yaml
import logging
import logging.config
import argparse
import filters
import sys

PORT = 57888
LDBPATH = "/p/lname/lname.db"
THREADS = 4
PASSWORD = os.environ.get('PHRAMPU_PASS')
USERNAME = os.environ.get('PHRAMPU_USER')
MACHINES = yaml.load(open('servers.yaml', 'r'))
MONGODB = 'mongodb://austinschwartz.com:27017/'
LOG_TO_MONGO = False

def configurelogging():
    with open('filters.yaml', 'r') as the_file:
        config_dict = yaml.load(the_file)

    logging.config.dictConfig(config_dict)
configurelogging()

def getargs(logger):
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

def log(*args):
    logging.info(*args)

def logerror(e):
    logging.error(e)
