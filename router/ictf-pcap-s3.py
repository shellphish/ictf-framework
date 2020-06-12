#!/usr/bin/env python

import sys
from subprocess import check_output, CalledProcessError, Popen
import logging
import logstash
import os
import signal
import re
import boto3
import yaml
import glob
from os.path import  join, basename
import threading
from time import sleep
sys.path.append(os.path.abspath(join(os.path.dirname(__file__), '..')))

SLEEP_TIME = 10

MAX_LOG_SIZE = "10" #MB
BASE_CAPTURE_DIR = "/opt/ictf/router/data"
SERVICES_CAPTURE_DIR = BASE_CAPTURE_DIR + "/services/"

OTHER_CAPTURE_DIR = BASE_CAPTURE_DIR + "/other/"
OTHER_CAPTURE_FILE = OTHER_CAPTURE_DIR + "ictf_other"

DEBUG_LOG_FILENAME = '/var/log/ictf-pcap-s3.log'

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
log = logging.getLogger('ictf-pcap-s3')
log.setLevel(logging.INFO)
log.addHandler(sh)
log.addHandler(fh)
log.addHandler(logstash.TCPLogstashHandler(LOGSTASH_IP, LOGSTASH_PORT, version=1))

class InterruptException(Exception):
    pass

def signal_handler(signal, frame):
    raise InterruptException("SIG-INT received, sending exception")

uploading = set()

def main():
    global uploading

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
            log.info("Starting TCPDUMP to s3 copier ")
            with open("aws_config.yml") as f:
                cfg = yaml.load(f)
                region = cfg["region"]
                access_key = cfg["access_key"]
                secret_key = cfg["secret_key"]
                bucket_name = cfg["bucket_name"]

            s3 = boto3.resource('s3', region_name=region,
                                aws_access_key_id=access_key,
                                aws_secret_access_key=secret_key)

            service_zips = glob.glob(SERVICES_CAPTURE_DIR + "*.gz")
            for fi in service_zips:
                if fi in uploading:
                    continue
                uploading.add(fi)
                log.info("copying file " + str(fi) + " to bucket " + str(bucket_name))
                s3.meta.client.upload_file(fi, bucket_name, basename(fi), Callback=ProgressPercentage(fi))

            other_zips = glob.glob(OTHER_CAPTURE_DIR + "*.gz")
            for fi in other_zips:
                if fi in uploading:
                    continue
                uploading.add(fi)
                log.info("copying file " + str(fi) + " to bucket " + str(bucket_name))
                s3.meta.client.upload_file(fi, bucket_name, basename(fi), Callback=ProgressPercentage(fi))

        except CalledProcessError as cpe:
            log.exception("Called Process Error: {}".format(cpe))
        except InterruptException:
            log.info("Recieved Signal interrupt")
            sys.exit(0)
        except Exception as e:
            log.exception("Caught exception {}".format(e))
            log.info("attempting to shutdown")

        log.info("Sleeping for " + str(SLEEP_TIME) + " seconds")
        sleep(SLEEP_TIME)


# taken from http://takwatanabe.me/boto3/generated/boto3.s3.transfer.html
class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        global uploading
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            log.debug(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))

            if self._size == self._seen_so_far:
                log.info("I'm going to get you, little file, " + self._filename)
                os.remove(self._filename)
                uploading.remove(self._filename)


def copy_done(value):
    log.info("at least 1 copy is complete")
    log.info(value)


if __name__ == "__main__":
    main()
