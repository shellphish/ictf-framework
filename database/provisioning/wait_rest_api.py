
import requests
import sys
import time

'''
 Waiting for the database REST api to show up!
'''
if __name__== "__main__":
    database_api_ip = sys.argv[1]  # ip of database passed from terraform script
    while True:
        try:
            ping_url = "http://" + database_api_ip + "/game/ping"
            result = requests.get(ping_url)
            if result.status_code is requests.status_codes.codes.OK:
                break
            else:
                time.sleep(10)
        except requests.exceptions.ConnectionError:
            time.sleep(10)
            continue









