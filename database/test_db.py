#!/usr/bin/python3

import subprocess
import requests
import sys
import threading
from time import sleep
from subprocess import Popen
import time

def getJASONResponse(query, data):
    try:
        r = requests.post(query, data)

        if r.status_code == 200:
            return r.json()

    except Exception as e:
        print(e)

    return None


def main():
    data = {
        'ctf_key': "FUNSTUFF",
        'root_key': "NOTFUNSTUFF",
        'ip': '172.31.64.22',
        'port': '1337'
    }

    url = "http://localhost/team/add/keys/2"
    print (getJASONResponse(url, data))


if __name__ == "__main__":
    main()
