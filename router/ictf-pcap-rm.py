#!/usr/bin/env python

import logging
import logstash
import os
import signal
import subprocess
import sys
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.world_constants import CfgKey

MAX_AGE_MIN = 30
SLEEP_TIME  = 10

MAX_LOG_SIZE = "10" #MB
BASE_CAPTURE_DIR = "/opt/ictf/router/data"
SERVICES_CAPTURE_DIR = BASE_CAPTURE_DIR + "/services/"

OTHER_CAPTURE_DIR = BASE_CAPTURE_DIR + "/other/"
OTHER_CAPTURE_FILE = OTHER_CAPTURE_DIR + "ictf_other"

DEBUG_LOG_FILENAME = '/var/log/ictf-pcap-rm.log'
LOGSTASH_PORT = 1717
LOGSTASH_IP = "localhost"

# set up formatting
formatter = logging.Formatter('[%(asctime)s] %(levelno)s (%(process)d) %(module)s: %(message)s')
# set up logging to STDOUT for all levels DEBUG and higher
sh = logging.StreamHandler(sys.stdout)
sh.setLevel(logging.INFO)
sh.setFormatter(formatter)
fh = logging.FileHandler(DEBUG_LOG_FILENAME)

# set up logging to a file for all levels DEBUG and higher
fh = logging.FileHandler(DEBUG_LOG_FILENAME)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)
log = logging.getLogger('MyLogger')
log.setLevel(logging.INFO)
log.addHandler(sh)
log.addHandler(fh)
log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))

class InterruptException(Exception):
    pass

def signal_handler(signal, frame):
    raise InterruptException("SIG-INT received, sending exception")

def main():
    if not os.path.exists(BASE_CAPTURE_DIR):
        os.makedirs(BASE_CAPTURE_DIR)
    if not os.path.exists(SERVICES_CAPTURE_DIR):
        os.makedirs(SERVICES_CAPTURE_DIR)
    if not os.path.exists(OTHER_CAPTURE_DIR):
        os.makedirs(OTHER_CAPTURE_DIR)

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)

    while True:
        try:
            log.info("Starting TCPDUMP remover...")
            subprocess.check_call(['find',  BASE_CAPTURE_DIR, '-type', 'f', '-mmin', '+' + str(MAX_AGE_MIN), '-delete'])
            subprocess.check_call(['find', OTHER_CAPTURE_DIR, '-type', 'f', '-mmin', '+' + str(MAX_AGE_MIN), '-delete'])
            log.info("Cleanup successful!")
        except subprocess.CalledProcessError as cpe:
            log.exception("Called Process Error: {}".format(cpe))
        except InterruptException:
            log.info("Recieved Signal interrupt")
            sys.exit(0)
        except Exception as e:
            log.exception("Caught exception {}".format(e))
            log.info("attempting to shutdown")
        log.info("Sleeping for " + str(SLEEP_TIME) + " seconds")
        time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
