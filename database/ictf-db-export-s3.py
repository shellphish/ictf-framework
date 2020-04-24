#!/usr/bin/env python

import sys
from subprocess import check_output, CalledProcessError, Popen
import logging
import os
import signal
import re
import boto3
import yaml
import glob
from os.path import  join, basename
import threading
from time import sleep
from filecmp import cmp as fcmp
sys.path.append(os.path.abspath(join(os.path.dirname(__file__), '..')))

SLEEP_TIME = 30

BACKUP_DIR = "/media/backups/ictf/"
BACKUPS_COPIED = join(BACKUP_DIR, "copies.dat")


DEBUG_LOG_FILENAME = '/var/log/ictf-db-export-s3.log'

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
log = logging.getLogger('dbexportlogger')
log.setLevel(logging.INFO)
log.addHandler(sh)
log.addHandler(fh)


class InterruptException(Exception):
    pass


def signal_handler(signal, frame):
    raise InterruptException("SIG-INT received, sending exception")


def main():

    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)
    open(BACKUPS_COPIED, "a+").write("Starting up process\n")
    while True:
        try:

            log.info("Starting DB Dump to s3 copier ")
            with open("aws_config.yml") as f:
                cfg = yaml.load(f)
                region = cfg["region"]
                access_key = cfg["access_key"]
                secret_key = cfg["secret_key"]
                bucket_name = cfg["bucket_name"]

            dumps = sorted(glob.iglob(BACKUP_DIR + "*.gz"), key=os.path.getctime, reverse=True)

            file_compare = False
            if len(dumps) > 0:
                if len(dumps) > 1:
                    file_compare = fcmp(dumps[0], dumps[1])

                if file_compare:
                    log.info("the two most recent files are identical, skipping copy. ")
                else:
                    newest_dump = dumps[0]
                    copied_files = open(BACKUPS_COPIED, "r").read().split("\n")
                    if newest_dump in copied_files:
                        log.info("skipping because already copied. ")
                    else:
                        s3 = boto3.resource('s3', region_name=region,
                                            aws_access_key_id=access_key,
                                            aws_secret_access_key=secret_key)
                        log.info("copying file " + str(newest_dump) + " to bucket " + str(bucket_name))
                        s3.meta.client.upload_file(newest_dump, bucket_name, basename(newest_dump),
                                                   Callback=ProgressPercentage(newest_dump))

        except CalledProcessError as cpe:
            log.exception(cpe)

        except InterruptException:
            log.info("Received Signal interrupt")
            sys.exit(0)
        except Exception as e:
            log.exception("Caught exception".format(e))

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
        # To simplify we'll assume this is hooked up
        # to a single filename.
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            log.info(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))

            if self._size == self._seen_so_far:
                log.info("Saving copied filename (" + self._filename + ")to copies.dat. " )
                #os.remove(self._filename)
                open(BACKUPS_COPIED,"a+").write(self._filename + "\n")


if __name__ == "__main__":
    main()
