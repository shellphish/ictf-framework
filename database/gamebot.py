import MySQLdb
import MySQLdb.cursors

import iso8601
import hashlib
import math
import time
import getopt
import pickle
import base64
import sys
import json
import random

from datetime import datetime, timedelta

from settings import MYSQL_DATABASE_USER, MYSQL_DATABASE_PASSWORD, MYSQL_DATABASE_DB


TICK_TIME_IN_SECONDS = 50

NUMBER_OF_BENIGN_SCRIPTS = 3
NUMBER_OF_GET_SET_FLAG_COMBOS = 1

def main():
    user = MYSQL_DATABASE_USER
    db_name = MYSQL_DATABASE_DB
    password = MYSQL_DATABASE_PASSWORD

    db = MySQLdb.connect(user=user, passwd=password, db=db_name, cursorclass=MySQLdb.cursors.DictCursor)

    c = db.cursor()

    current_tick, seconds_left = get_current_tick(c)
    if current_tick != 0:
        print "We must be picking up from the last run. Sleep for", seconds_left, "until the next tick."
        time.sleep(seconds_left)

    team_ids = get_team_ids(c)
    service_ids = get_service_ids(c)

    while True:
        # Create a new tick
        current = datetime.now()

        time_to_sleep = random.uniform(TICK_TIME_IN_SECONDS - 30, TICK_TIME_IN_SECONDS + 30)

        time_to_change = current + timedelta(seconds=time_to_sleep)
        c.execute("""insert into ticks (time_to_change, created_on) values(%s, %s)""", (time_to_change.isoformat(), current.isoformat(),))
        tick_id = db.insert_id()

        print "tick", tick_id

        num_benign_scripts = random.randint(max(1, NUMBER_OF_BENIGN_SCRIPTS - 2), NUMBER_OF_BENIGN_SCRIPTS + 2)


        # Decide what scripts to run against each team
        for team_id in team_ids:
            list_of_scripts_to_execute = get_list_of_scripts_to_run(c, tick_id, team_id, service_ids, num_benign_scripts)

            c.execute("""insert into team_scripts_run_status (team_id, tick_id, json_list_of_scripts_to_run, created_on)
                         values (%s, %s, %s, %s)""",
                      (team_id, tick_id, json.dumps(list_of_scripts_to_execute), datetime.now().isoformat()))

            
        # Commit everything to the db
        db.commit()        
        

        # Sleep for the amount of time until the next tick

        time_diff_to_sleep = time_to_change - datetime.now()
        seconds_to_sleep = time_diff_to_sleep.seconds + (time_diff_to_sleep.microseconds/1E6)

        if time_diff_to_sleep.total_seconds() < 0:
            print time_diff_to_sleep
            seconds_to_sleep = 0

        print "Sleeping for", seconds_to_sleep
        time.sleep(seconds_to_sleep)
        print "Awake"

def get_list_of_scripts_to_run(c, tick_id, team_id, service_ids, num_benign_scripts):
    scripts_to_run = []

    # we want to run all the set flags first, then a random mix of benign and get flags
    set_flag_scripts = []
    get_flag_scripts = []
    benign_scripts = []

    for service_id in service_ids:
        c.execute("""select id, is_ours, type, team_id, service_id, is_working, latest_script from scripts where service_id = %s and is_working = 1 and latest_script = 1""",
                  (service_id,))
        results = c.fetchall()

        benigns = []
        
        for result in results:
            the_type = result['type']
            the_id = result['id']
            if the_type == 'getflag':
                get_flag_scripts.append(the_id)
            elif the_type == 'setflag':
                set_flag_scripts.append(the_id)
            elif the_type == 'benign':                
                benigns.append(the_id)
            elif the_type == 'exploit':
                assert False, "In this version, we should never be running exploits"

        for i in xrange(num_benign_scripts):
            if benigns:
                benign_script = random.choice(benigns)
                benign_scripts.append(benign_script)

    random.shuffle(set_flag_scripts)

    scripts_to_run.extend(set_flag_scripts)

    other_scripts = []
    other_scripts.extend(get_flag_scripts)
    other_scripts.extend(benign_scripts)
    random.shuffle(other_scripts)

    scripts_to_run.extend(other_scripts)

    return scripts_to_run

def get_team_ids(c):
    c.execute("""select id from teams""")

    return set(r['id'] for r in c.fetchall())

def get_service_ids(c):
    c.execute("""select id from services""")

    return set(r['id'] for r in c.fetchall())

def get_current_tick(c):
    c.execute("""select id, time_to_change, created_on from ticks order by created_on desc limit 1""")
    result = c.fetchone()
    current_tick = 0
    seconds_left = 1337
    if result:
        current_tick = result['id']
        current_time = iso8601.parse_date(datetime.now().isoformat())
        time_to_change = iso8601.parse_date(result['time_to_change'])
        
        seconds_left = (time_to_change - current_time).total_seconds()
        if seconds_left < 0:
            seconds_left = 0
        
    return current_tick, seconds_left


if __name__ == "__main__":
    sys.exit(main())
