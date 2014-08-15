import MySQLdb
import MySQLdb.cursors
import subprocess
import json
import os
import os.path
import imp
import base64
import random
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
# first, run the database.sql schema to wipe everything

def run_command(command):
    return subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).communicate()

def init_database():
    luca_user = 'flask'
    luca_pass = 'whygodwhy'
    luca_host = '127.0.0.1'
    luca_port = 5002
    luca_db = 'ictf_registration_dec_2013'

    my_user = MYSQL_DATABASE_USER
    my_db = MYSQL_DATABASE_DB

    result = run_command("mysql -u " + my_user + " -p" + MYSQL_DATABASE_PASSWORD + " " + my_db + " < database.sql")
    to_return = str(result)

    luca_db = MySQLdb.connect(host=luca_host, user=luca_user, port=luca_port, passwd=luca_pass, db=luca_db, cursorclass=MySQLdb.cursors.DictCursor)

    my_db = MySQLdb.connect(user=my_user, passwd=MYSQL_DATABASE_PASSWORD, db=my_db, cursorclass=MySQLdb.cursors.DictCursor)

    luca_c = luca_db.cursor()

    luca_c.execute("""select * from team""");

    my_c = my_db.cursor()
    team_ids = []

    # Very first, create the game
    
    new_game_id = random.randint(0, 1000000)
    my_c.execute("""insert into game (id) values (%s)""",
                 (new_game_id,))

    # First, create the levels

    level_name_to_id = [("mining", 1), ("refining", 2), ("build", 3), ("launch", 4)] 
    #level_name_to_id = [("all_active_all_the_time", 1), ("all_active_all_the_time_2",2), ("all_active_all_the_time_3", 3), ("all_active_all_the_time_4", 4)]
    level_score_mapping = {1: 6000, 2: 4500, 3: 3000, 4: 666666666}
    for level, level_id in level_name_to_id:
        print level, level_id
        my_c.execute("""insert into levels (id, name, created_on) values (%s, %s, %s)""",
                     (level_id, level, datetime.now().isoformat()))

        my_c.execute("""insert into level_score_limit (level_id, score_limit, created_on) values (%s, %s, %s)""",
                     (level_id, level_score_mapping[level_id], datetime.now().isoformat()))

    # The first level has an active state of "Start"
    my_c.execute("""insert into level_active_state (level_id, active_state, created_on) values (%s, %s, %s)""",
                 (1, 'Start', datetime.now().isoformat()))

    for result in luca_c.fetchall():
        if (result['is_rejected'] == False and result['faculty_email_confirm'] == True and result['academic_confirm'] == True and result['faculty_confirm'] == True):
            to_return += str(result) + "\n"
            exec_result = my_c.execute("""insert into teams (team_name, team_size, team_country, team_address, team_logo, university_name, university_url, ip_range, created_on, id)
                                          values(%s, %s, %s, %s, %s, %s, %s, '127.0.0', %s, %s)""", 
                                       (result['team_name'], result['team_size'], result['team_country'], result['team_address'], 'http://ictf2013.info/team_logo/' + str(result['id']), result['university_name'],
                                        result['university_url'], datetime.now().isoformat(), result['id']))

            team_ids.append(my_db.insert_id())
            # set team's score to zero 
            team_id = my_db.insert_id()
            for level, level_id in level_name_to_id:
                my_c.execute("""insert into team_score (team_id, score, reason, level_id, created_on) values (%s, 0, 'Initial Score', %s, %s)""",
                         (team_id, level_id, datetime.now().isoformat()))

            # set the team's level to the first level
            my_c.execute("""insert into team_level (team_id, level_id, created_on) values (%s, 1, %s)""",
                         (team_id, datetime.now().isoformat()))

            # set the team's credits to 0
            my_c.execute("""insert into team_credits (team_id, credits, reason, created_on) values (%s, 0, 'Initial credits', %s)""",
                         (team_id, datetime.now().isoformat()))

            my_db.ping()
            to_return += str(my_db.insert_id()) + "\n"


    # insert all services
    create_all_services_and_scripts(my_c, my_db)
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


    # Now we need to create all the merch the teams can buy
    MAX_WINS = 100000
    current_time = datetime.now().isoformat()
    my_c.executemany("""insert into merch (id, name, description, min_bid, num_winners, max_wins, extra_info, created_on)
                    values (%s, %s, %s, %s, %s, %s, %s, %s)""",
                 [
                   (1, "protection", "This bonus makes your team immune from attack for the next tick.", 5, 2, 60, None, current_time),
                   (2, "purchase exploit", "Purchase the ZDI exploit for a given service.", 5000, 1, 1, "exploit", current_time),
                   (3, "show attack netflow", "Show, in the last tick which netflow was an attack. If there was no attack, it will say that.", 50, 2, 60, None, current_time),
                   (4, "sabotage exploit", "Bribe ZDI to not run a team's exploit in the next tick. Send them a message to let them know how much you care.", 10, 2, 60, "team", current_time)
                 ])
                  

    my_db.commit()
    return to_return

import os
def create_all_services_and_scripts(c, db):
    possible_services = os.listdir('../services')
    for possible in possible_services:
        db.ping()

        service_dir = '../services/' + possible + '/'
        print "trying", possible
        try: 
          with open(service_dir + 'info.json') as service_info:
                info = json.load(service_info)
		print info
                if info['is_working'] == 1:
                    authors_string = ""
                    if 'authors' in info:
                        authors_string = ", ".join(info['authors'])
                    description = info.get('service_description', "")
                    flag_id_description = info.get('flag_id_description', "")
                    service_id = create_service(info['id'], info['name'], info['port'], authors_string, description, flag_id_description, c, db)
                    create_script(service_id, 'getflag', service_dir + info['getflag'], c, db)
                    create_script(service_id, 'setflag', service_dir + info['setflag'], c, db)
                    for benign in info['benign']:
                        create_script(service_id, 'benign', service_dir  + benign, c, db)
                    for exploit in info['exploit']:
                        create_script(service_id, 'exploit', service_dir + exploit, c, db)
                print "imported", possible
        except IOError as e:
            print "service dir " + possible + " doesn't have info.json" + str(e)
        except ValueError as e:
            print "service dir " + possible + " has wrong info.json" + str(e)


def create_service(id, name, port, authors, description, flag_id_description, c, db):
    db.ping()
    
    c.execute("""insert into services (id, name, port, authors, description, flag_id_description, created_on) values (%s, %s, %s, %s, %s, %s, %s)""",
              (id, name, port, authors, description, flag_id_description, datetime.now().isoformat()))
    
    return db.insert_id()

def create_script(service_id, type, script_location, c, db):
    db.ping()
    name = os.path.basename(script_location)

    with open(script_location) as script_file:
        script = script_file.read()
        c.execute("""insert into scripts (name, is_ours, is_bundle, type, service_id, is_working, created_on, latest_script)
                     values (%s, 1, 0, %s, %s, 1, %s, 1)""",
                  (name, type, service_id, datetime.now().isoformat()))
        script_id = db.insert_id()
        c.execute("""insert into script_payload (script_id, payload, created_on) values (%s, %s, %s)""",
                  (script_id, base64.b64encode(script), datetime.now().isoformat()))


if __name__ == "__main__":
    print init_database()
