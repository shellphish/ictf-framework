import MySQLdb
import MySQLdb.cursors
import subprocess
import json
import os
import os.path
import base64
import random
import sys
from datetime import datetime

from settings import *

class DB:
    conn = None

    def connect(self, **kwargs):
        self.conn = MySQLdb.connect(**kwargs)

    def query(self, sql):
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql)
        except (AttributeError, MySQLdb.OperationalError):
            self.connect()
            cursor = self.conn.cursor()
            cursor.execute(sql)
        return cursor



def run_command(command):
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

def init_database(num_teams, services_info):
    my_user = MYSQL_DATABASE_USER
    my_db = MYSQL_DATABASE_DB
    # first, run the database.sql schema to wipe everything
    result = run_command("mysql -u " + my_user + " -p" + MYSQL_DATABASE_PASSWORD + " " + my_db + " < database.sql")
    to_return = str(result)

    my_db = MySQLdb.connect(user=my_user, passwd=MYSQL_DATABASE_PASSWORD, db=my_db, cursorclass=MySQLdb.cursors.DictCursor)

    my_c = my_db.cursor()

    team_ids = []

    # Very first, create the game
    new_game_id = random.randint(0, 1000000)
    my_c.execute("""insert into game (id) values (%s)""",
                 (new_game_id,))

    for i in xrange(num_teams):
        team_num = i + 1
        team_name = "Team %s" % team_num
        team_ip_range = "10.0.%s" % team_num
        exec_result = my_c.execute("""insert into teams (team_name, ip_range, created_on) values(%s, %s, %s)""", 
                                   (team_name, team_ip_range, datetime.now().isoformat()))

        team_ids.append(my_db.insert_id())
        # set team's score to zero 
        team_id = my_db.insert_id()
        my_c.execute("""insert into team_score (team_id, score, reason, created_on) values (%s, 0, 'Initial Score', %s)""",
                     (team_id, datetime.now().isoformat()))

        my_db.ping()
        to_return += str(my_db.insert_id()) + "\n"


    # insert all services
    create_all_services_and_scripts(my_c, my_db, services_info)
    my_db.ping()
    # set all the services as up
    my_c.execute("""select * from services""")
    services = my_c.fetchall()

    for team_id in team_ids:
        my_db.ping()
        for service in services:
            my_c.execute("""insert into team_service_state(team_id, service_id, state, reason, created_on) 
                            values (%s, %s, 2, 'Initial state', %s)""",
                         (team_id, service['id'], datetime.now().isoformat()))

    my_db.commit()
    return to_return

import os
def create_all_services_and_scripts(c, db, services_info):
    for service_info in services_info:
        try:
            db.ping()
            if service_info['is_working'] == 1:
                authors_string = ""
                if 'authors' in service_info:
                    authors_string = ", ".join(service_info['authors'])
                description = service_info.get('service_description', "")
                flag_id_description = service_info.get('flag_id_description', "")
                service_id = create_service(service_info['name'], service_info['port'], authors_string, description, flag_id_description, c, db)

                create_script(service_id, 'getflag', service_info['getflag'], c, db)
                create_script(service_id, 'setflag', service_info['setflag'], c, db)
                for benign in service_info['benign']:
                    create_script(service_id, 'benign', benign, c, db)
                print "imported", service_info['name']

        except ValueError as e:
            print "service dir " + possible + " has wrong info.json" + str(e)


def create_service(name, port, authors, description, flag_id_description, c, db):
    db.ping()
    
    c.execute("""insert into services (name, port, authors, description, flag_id_description, created_on) values (%s, %s, %s, %s, %s, %s)""",
              (name, port, authors, description, flag_id_description, datetime.now().isoformat()))
    
    return db.insert_id()

def create_script(service_id, type, script, c, db):
    db.ping()
    name = type + ".py"
    c.execute("""insert into scripts (name, is_ours, is_bundle, type, service_id, is_working, created_on, latest_script)
                 values (%s, 1, 0, %s, %s, 1, %s, 1)""",
              (name, type, service_id, datetime.now().isoformat()))
    script_id = db.insert_id()
    c.execute("""insert into script_payload (script_id, payload, created_on) values (%s, %s, %s)""",
              (script_id, script, datetime.now().isoformat()))


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print "usage: %s <num_teams>"
        sys.exit(-1)

    num_teams = int(sys.argv[1])

    # now, read the serialized version of the service_infos

    with open("/opt/database/combined_info.json") as f:
        services_info = json.load(f)

    print init_database(num_teams, services_info)
