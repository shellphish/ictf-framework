#!/usr/bin/env python

import sys
from subprocess import check_output, CalledProcessError, Popen
import logging
import logstash
import os
import signal
import re
import yaml
from os.path import join, basename

sys.path.append(os.path.abspath(join(os.path.dirname(__file__), '..')))

# with open("aws_router_config.yml") as f:
#     cfg = yaml.load(f)['instance']
GAME_ID = "0"

MAX_LOG_SIZE = "200" #MB
BASE_CAPTURE_DIR = "/opt/ictf/router/data"
SERVICES_CAPTURE_DIR = BASE_CAPTURE_DIR + "/services/"
SERVICES_CAPTURE_FILE = SERVICES_CAPTURE_DIR + GAME_ID + "_serviceports"

OTHER_CAPTURE_DIR = BASE_CAPTURE_DIR + "/other/"
OTHER_CAPTURE_FILE = OTHER_CAPTURE_DIR + GAME_ID + "_otherports"

DEBUG_LOG_FILENAME = '/var/log/ictf-tcp-dump-service.log'

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

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    '''
    alist.sort(key=natural_keys) sorts in human order
    http://nedbatchelder.com/blog/200712/human_sorting.html
    (See Toothy's implementation in the comments)
    '''
    return [ atoi(c) for c in re.split('(\d+)', text) ]

CMD_TCPDUMP = ['tcpdump']
# CMD_TCPDUMP += ['-s0']                  # max snapshot length to avoid truncating packet
CMD_TCPDUMP += ['-n']                   # don't resolve names
CMD_TCPDUMP += ['-i', 'any']            # all interfaces, we filter by netmask and portrange
CMD_TCPDUMP += ['-Z', 'root']           # drop privs to root, don't really know why this is here
CMD_TCPDUMP += ['-C', MAX_LOG_SIZE]     # rotate every MAX_LOG_SIZE MB of data (currently 500MB)
CMD_TCPDUMP += ['-G', '600']            # rotate every 10 minutes
CMD_TCPDUMP += ['-w', SERVICES_CAPTURE_FILE + "_%Y-%m-%d_%H-%M-%S_0"]
CMD_TCPDUMP += ['-z', '/opt/ictf/router/pcap-mv.sh']
CMD_TCPDUMP += 'tcp and not net 10.9.0.1 mask 255.255.0.255 and portrange 10000-10100'.split()
def main():

    if not os.path.exists(BASE_CAPTURE_DIR):
        os.makedirs(BASE_CAPTURE_DIR)
    if not os.path.exists(SERVICES_CAPTURE_DIR):
        os.makedirs(SERVICES_CAPTURE_DIR)
    if not os.path.exists(OTHER_CAPTURE_DIR):
        os.makedirs(OTHER_CAPTURE_DIR)

    proc_servs = None

    try:
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGABRT, signal_handler)

        log.info("Starting TCPDUMP runner")
        while True:
            try:
                log.info("Executing TCPDUMP Command " + str(CMD_TCPDUMP))
                proc_servs = Popen(CMD_TCPDUMP)

                proc_servs.wait()

            except CalledProcessError as cpe:
                log.exception("Called Process Error: {}".format(cpe))
            except InterruptException:
                log.info("Recieved Signal interrupt")
                if proc_servs is not None:
                    proc_servs.kill()
                log.info("attempting to kill any remaining tcpdumps")
                cmd = ['pkill', '-9', 'tcpdump']
                Popen(cmd)
                sys.exit(0)

    except Exception as e:
        log.exception("Caught exception: {}".format(e))
        log.info("attempting to shutdown")
        cmd = ['pkill', '-9', 'tcpdump']
        Popen(cmd)

    # log.info("Zip any remaining files")
    # zf = zipfile.ZipFile(ZIP_FILE, "w", zipfile.ZIP_DEFLATED)
    # caps = glob.glob(BASE_CAPTURE_DIR + "/" + BASE_CAPTURE_NAME + "*")
    # for i in range(0, len(caps)):
    #     absname = os.path.abspath(caps[i])
    #     arcname = absname[len(BASE_CAPTURE_DIR) + 1:]
    #     log.info('zipping %s as %s' % (caps[i], arcname))
    #     zf.write(absname, arcname)
    #     #os.remove(caps[i])
    # zf.close()


if __name__ == "__main__":
    main()
