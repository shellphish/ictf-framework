#!/usr/bin/env python2.7

import logging
import os
import requests
import subprocess
import sys
import time
sys.path.insert(0,"/var/www/framework")
import secrets

while True:
    try:
        games = requests.get('http://ictf.cs.ucsb.edu/framework/ctf/pending?secret='+secrets.API_SECRET).json()
        if 'ctf_hash' in games:
            print "Spawning the creator for", games['ctf_hash']
            subprocess.Popen("./create_vms.py "+games['ctf_hash'], shell=True)
    except:
        print "Exception while getting the pending CTF or spawning its creation!"
    time.sleep(30)
