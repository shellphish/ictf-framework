#!/usr/bin/python

'''
poller.py: retrieve info about the current status of a CTF game
by polling at regular interval a central DB and store the
received info in a redis-based queue.
'''


__author__ = "Nilo Redini"
__email__ = "nredini@cs.ucsb.edu"

import time
import redis
import requests
import sys
import json
import functools

from requests.exceptions import ConnectionError


DEBUG = True

# we use the last tick since some info may not be updated in
# the current tick.
last_tick = 0
current_tick = 0
init_web_interface = True

def guard(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print "[!] Error: " + str(e)
            return None
    return wrapper


#@guard
def should_get_data(game_db):
    global last_tick
    global current_tick
    global init_web_interface

    query_db = False

    # get the tick from the DB
    tick_endpoint = config['tick_endpoint']['e']
    tick_key = config['tick_endpoint']['key']

    try:
        data = game_db.get(db_endpoint + tick_endpoint, params=db_request_params)
    except ConnectionError:
        return False

    if data.status_code != 200:
        return False

    data = data.json()
    recv_tick = data[tick_key] if tick_key else data

    # decide whether to query the db or not
    if init_web_interface and recv_tick == 0:
        # When the game starts we have to show something
        query_db = True
        init_web_interface = False
    elif current_tick != recv_tick:
        if DEBUG:
            print "[*] Tick Changed: " + str(recv_tick)
        last_tick = recv_tick - 1
        current_tick = recv_tick
        query_db = True

    return query_db


#@guard
def set_game_info(cache, game_db):
    # Get the current state of the game
    data = {}

    # requesting latest endpoints
    for v in config['dynamic_endpoints']['latest']:
        if DEBUG:
            print "[*] Requesting " + v
        tmp = game_db.get(db_endpoint + v, params=db_request_params).json()
        data.update(tmp)
        if DEBUG:
            print "[*] Updated " + ''.join(tmp.keys())

    # requesting previous endpoints
    for v in config['dynamic_endpoints']['previous_tick']:
        if DEBUG:
            print "[*] Requesting " + v
        tmp = game_db.get(db_endpoint + v + str(last_tick), params=db_request_params).json()
        data.update(tmp)
        if DEBUG:
            print "[*] Updated " + ''.join(tmp.keys())

    # add the tick
    tick_endpoint = config['tick_endpoint']['e']
    tick = game_db.get(db_endpoint + tick_endpoint, params=db_request_params).json()
    data.update({'tick': tick})
    cache.lpush(str(config['redis_db_id']), json.dumps(data))


#@guard
def should_update_game_static_info(game_db):
    query_db = True

    print "Refreshing game info "
    # get team info from the DB
    static_endpoint = config['game_start']['stat']
    # game_key = 'id'
    try:
        data = game_db.get(db_endpoint + static_endpoint, params=db_request_params)
    except ConnectionError:
        return False

    if data.status_code != 200:
        return False

    data = data.json()
    # decide whether to refresh game info or not
    if config['game_start']['key'] in data and  data[config['game_start']['key']]=="621":
        query_db=False
    else:
        if DEBUG:
            print "[*] game info refreshed "

    return query_db


#@guard
def set_game_static_info(cache, game_db):
    # Get the static data of the game
    data = {}
    # print "setting game static info"
    for v in config['static_endpoints']:
        tmp = game_db.get(db_endpoint + v, params=db_request_params).json()
        print tmp
        data.update(tmp)
    cache.set('static', json.dumps(data))

#@guard
def set_game_tick(cache, game_db):
    data = game_db.get(db_endpoint + config['tick_endpoint']['e'], params=db_request_params).json()
    cache.set('tick', json.dumps(data))
    print "[*] Updated tick " + str(data['tick_id'])

def run_forever():
    redis_params = {
        "host": config['redis_host'],
        "port": config['redis_port'],
        "db": config['redis_db_id']
    }

    cache = redis.StrictRedis(**redis_params)
    game_db = requests.Session()
    
    if should_update_game_static_info(game_db):
        set_game_static_info(cache, game_db)

    while True:
        while not should_get_data(game_db):
            print('.'),
            time.sleep(config['polling_sleep_time'])
        if(should_update_game_static_info(game_db)) :
           set_game_static_info(cache, game_db)
        set_game_tick(cache, game_db)
        time.sleep(config['setup_sleep_time'])
        set_game_info(cache, game_db)

config = None
db_endpoint = None
db_request_params = None
if __name__ == "__main__":
    if len(sys.argv) < 2:
        msg = "Usage: " + sys.argv[0] + " config_file"
        sys.exit(msg)

    print "[*] Starting " + sys.argv[0]
    with open(sys.argv[1]) as data_file:
        config = json.load(data_file)

    db_endpoint = "http://" + config['db_endpoint']# + ":" + str(config['db_port'])
    db_request_params = {"secret": config['secret']}
    run_forever()
