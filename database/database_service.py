import json
import MySQLdb
import MySQLdb.cursors
import random
import datetime
import iso8601
import base64
import string
import time
import math


from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
app = Flask(__name__)
app.config.from_object('settings')

from flaskext.mysql import MySQL
mysql = MySQL()
mysql.init_app(app)


@app.route("/")
def hello():
    return render_template('homescreen.html')

@app.route("/state")
def current_state():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    # first, get the current state

    current_tick, seconds_to_next_tick = get_current_tick(c)

    result = {}
    result['state_id'] = current_tick
    result['state_expire'] = seconds_to_next_tick


    
    c.execute("""select id from game limit 1""")
    result['game_id'] = c.fetchone()['id']

    
    c.execute("""select services.id as service_id, services.name as service_name, services.port as port from services;""")
    result['services'] = c.fetchall()
    
    # need to decide what scripts to run

    c.execute("""select scripts.id as script_id, scripts.is_bundle as is_bundle, scripts.name as script_name, scripts.type as type, scripts.service_id as service_id from scripts""")

    result['scripts'] = c.fetchall()

    c.execute("""select team_scripts_run_status.team_id as team_id, team_scripts_run_status.json_list_of_scripts_to_run as json_list from team_scripts_run_status where team_scripts_run_status.tick_id = %s""", (current_tick,))

    run_scripts = []
    
    for team_scripts_to_run in c.fetchall():
        team_id = team_scripts_to_run['team_id']
        json_list = team_scripts_to_run['json_list']

        list_of_services = json.loads(json_list)

        run_scripts.append({'team_id': team_id,
                            'run_list': list_of_services})

    result['run_scripts'] = run_scripts

    
    return json.dumps(result)


@app.route("/getgameinfo")
def get_game_info():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    result = {}
    c.execute("""select id as team_id, team_name, team_logo as logo, team_country as country, ip_range from teams""");
    result['teams'] = c.fetchall()

    c.execute("""select id as service_id, name as service_name, port, flag_id_description, description from services""");
    result['services'] = c.fetchall()

    return json.dumps(result)

@app.route("/getstate/<teamid>")
def get_state(teamid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    result = {}
    result['service_state'] = {}
    c.execute("""select services.id as service_id, (select state from team_service_state where team_id = %s and services.id = service_id order by created_on desc limit 1) as state from services""", (teamid,))
    
    for res in c.fetchall():
        result['service_state'][res['service_id']] = res['state']

    return json.dumps(result)

@app.route("/getservicesstate")
def get_services_state():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    current_tick, time_left = get_current_tick(c)

    teams = get_services_state_by_tick(current_tick, c)

    return json.dumps({"teams": teams})

@app.route("/getservicesstate/<tick_id>")
def get_services_state_tick(tick_id):
    # TODO: FIX ME
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    teams = get_services_state_by_tick(tick_id, c)

    return json.dumps({"teams": teams})


def get_services_state_by_tick(tick_id, c):

    # Get the timeframes of the tick
    c.execute("""select created_on, time_to_change from ticks where id = %s""",
              tick_id)
    result = c.fetchone()
    tick_start_time = result['created_on']
    tick_end_time = result['time_to_change']

    c.execute("""select id from teams""")
    teams = []

    for result in c.fetchall():
        team_id = result['id']
        c.execute("""select id from services""")
        
        services = []
        for result in c.fetchall():
            service_id = result['id']
            c.execute("""select state from team_service_state where team_id = %s and service_id = %s and created_on > %s and created_on < %s""",
                      (team_id, service_id, tick_start_time, tick_end_time))
            service_status = -1
            service_statuses = []
            for result in c.fetchall():
                service_statuses.append(result['state'])
                
            if len(service_statuses) != 0:
                service_status = min(service_statuses)
            services.append({'service_id': service_id, 'state': service_status})

        teams.append({"team_id" : team_id, "services": services})
    return teams


@app.route("/servicestate")
def get_services_exploit_state():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select id, name from services""")

    services = []
    for result in c.fetchall():
        service_id = result['id']
        service_name = result['name']


        # decide who got first blood
        c.execute("""select tick_id from team_exploited_service where service_id = %s and was_successful = 1 and was_detected = 0 order by tick_id limit 1""",
                  (service_id,))
        result = c.fetchone()
        
        first_blood = []
        if result:
            winning_tick = result['tick_id']
            c.execute("""select distinct(attacking_team_id) from team_exploited_service where service_id = %s and was_successful = 1 and was_detected = 0 and tick_id = %s""",
                      (service_id, winning_tick))
            for result in c.fetchall():
                first_blood.append({'team_id': result['attacking_team_id'], 'tick_id': winning_tick})


        overall_detection_number = 0
        overall_missed_number = 0
        
        overall_successful_number = 0
        overall_unsuccessful_number = 0
        
        
        c.execute("""select id from teams""")
        
        teams_exploited = []
        for result in c.fetchall():
            team_id = result['id']

            c.execute("""select was_successful, was_detected from team_exploited_service where attacking_team_id = %s and service_id = %s""",
                      (team_id, service_id))

            times_successfully_undetected = 0
            times_successfully_exploited = 0
            times_unsuccessfully_exploited = 0

            for result in c.fetchall():
                was_successful = result['was_successful']
                was_detected = result['was_detected']
                if was_successful and not was_detected:
                    times_successfully_undetected += 1
                    
                if was_successful:
                    times_successfully_exploited += 1
                    overall_successful_number += 1
                if not was_successful:
                    times_unsuccessfully_exploited += 1
                    overall_unsuccessful_number += 1

            times_detected = 0
            times_undetected = 0

            c.execute("""select was_detected, was_successful from team_exploited_service where defending_team_id = %s and service_id = %s""",
                      (team_id, service_id))
            for result in c.fetchall():
                was_successful = result['was_successful']
                was_detected = result['was_detected']
                if was_detected and was_successful:
                    times_detected += 1
                    overall_detection_number += 1
                if was_successful and not was_detected:
                    times_undetected += 1
                    overall_missed_number += 1

            teams_exploited.append({"team_id": team_id, "times_successfully_undetected": times_successfully_undetected, "times_successfully_exploited": times_successfully_exploited, "times_unsuccessfully_exploited": times_unsuccessfully_exploited, "times_detected": times_detected, "times_undetected": times_undetected})


        # Who purchased an exploit for this service?
        purchased_exploit = []
        c.execute("""select team_id from team_merch_results where extra_info = %s and merch_id = 2""",
                  (service_id,))
        for result in c.fetchall():
            team_id = result['team_id']

            purchased_exploit.append({'team_id': team_id})

        
        overall_detection_rate = -1
        if (overall_missed_number + overall_detection_number) != 0:
            overall_detection_rate = (1.0 * overall_detection_number / (overall_missed_number + overall_detection_number)) * 100

        overall_success_rate = -1
        if (overall_successful_number + overall_unsuccessful_number) != 0:
            overall_success_rate = (1.0 * overall_successful_number / (overall_successful_number + overall_unsuccessful_number)) * 100

        c.execute("""select SUM(is_up) as total_up, count(id) as total from team_service_tick_status where service_id = %s""",
                  (service_id,))
        service_up_rate = 0
        result = c.fetchone()
        if result:
            total = int(result['total'] or 0)
            total_up = int(result['total_up'] or 0)

            service_up_rate = -1
            if total != 0:
                service_up_rate = 100 * ((total_up * 1.0) / total)

        services.append({ "service_id": service_id, "service_name": service_name, "first_blood": first_blood, "teams_exploited": teams_exploited, "purchased_exploit": purchased_exploit, "overall_detection_rate": int(overall_detection_rate), "overall_success_rate": int(overall_success_rate), "service_up_rate": int(service_up_rate)})

    return json.dumps({"services": services})

@app.route("/attack/<tick_id>")
def get_attacks(tick_id):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()


    attacks = []
    for i in xrange(1, random.randint(1, 10)):
        attacks.append({ "attacker_team_id" : random.randint(1, 100),
                  "defender_team_id" : random.randint(1, 100),
                  "service_id" : random.randint(1, 7),
                  "was_successful": random.randint(0, 1),
                  "was_detected" : random.randint(0, 1),
                  "num_times_attacker_attacked_defender": random.randint(0, 2000),
                  "num_times_attacker_successfully_attacked_defender": random.randint(0, 2000),
                  "num_times_defender_attacked_attacker": random.randint(0, 2000),
                  "num_times_defender_successfully_attacked_attacker": random.randint(0, 2000),
                  "num_times_defender_detected": random.randint(0, 2000),
                  "num_times_attacker_detected": random.randint(0, 2000) })

    return json.dumps({"attacks": attacks})


@app.route("/setservicestate/<teamid>/<serviceid>", methods=['GET'])
def set_state(teamid, serviceid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    status = int(request.args.get('status'))
    reason = request.args.get('reason')
    if not (status == 2 or status == 1 or status == 0):
        abort(400)

    c = mysql.get_db().cursor()
    c.execute("""insert into team_service_state (team_id, service_id, state, reason, created_on) 
                 values (%s, %s, %s, %s, %s)""",
              (teamid, serviceid, status, reason, datetime.datetime.now().isoformat()))

    result = {"result": "great success"}
    mysql.get_db().commit()

    return json.dumps(result)

@app.route("/netflows/<teamid>")
def get_netflows_for_team(teamid):
    PAST_MIN_TO_GET = 5

    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    lasttime = datetime.datetime.now() - datetime.timedelta(minutes=PAST_MIN_TO_GET)

    c = mysql.get_db().cursor()

    c.execute("""select created_on from ticks where is_first_of_round = 1 order by created_on desc limit 1""")
    start_of_the_round = c.fetchone()['created_on']


    current_time = iso8601.parse_date(datetime.datetime.now().isoformat())
    start_of_round_time = iso8601.parse_date(start_of_the_round)
    seconds_since_start = (current_time - start_of_round_time).total_seconds()

    c.execute("""select id, source_ip, source_port, dest_ip, dest_port, created_timestamp, marked_status from netflows where team_id = %s and created_on > %s order by id desc""",
              (teamid, start_of_the_round))
    return json.dumps({'netflows' : c.fetchall(), 'netflows_in_last_n_seconds' : seconds_since_start})
              


@app.route("/addnetflow/<teamid>/<serviceid>", methods=['GET'])
def add_net_flow(teamid, serviceid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    # HACK TO FIX 
    srcip = "10.13." + str(teamid) + ".1"

    srcport = request.args.get('source_port')
    destip = request.args.get('dest_ip')
    destport = request.args.get('dest_port')
    created_timestamp = request.args.get('timestamp')
    session = request.args.get('session')
    scriptid = request.args.get('script_id')


    c = mysql.get_db().cursor()

    c.execute("""select type from scripts where id = %s limit 1""",
                       (scriptid,))

    result = c.fetchone()
    
    is_malicious = result['type'] == 'exploit'


    # insert and return the ID
    res = c.execute("""insert into netflows (team_id, service_id, source_ip, source_port, dest_ip, dest_port, is_malicious, created_timestamp, session, created_on, script_id)
                       values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (teamid, serviceid, srcip, srcport, destip, destport, is_malicious, created_timestamp, session, datetime.datetime.now().isoformat(), scriptid))
    if not res:
        abort(400)

    netflowid = mysql.get_db().insert_id()

    result = {'id' : netflowid, 'result': 'great success'}

    mysql.get_db().commit()
    return json.dumps(result)    

@app.route("/markmalicious/<teamid>/<netflowid>")
def mark_malicious(teamid, netflowid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    result = {}

    # check to make sure they didn't already try this one
    c.execute("""select count(id) as count from team_guesses where team_id = %s and netflow_id = %s""",
              (teamid, netflowid,))

    count = c.fetchone()['count']
    if count != 0:
        result['result'] = 'error'
        result['reason'] = "You already claimed that netflow as malicious"
        return json.dumps(result)

    # check and see if the netflowid is actually malicious
    c.execute("""select team_id, service_id, session, is_malicious, created_timestamp from netflows where id = %s limit 1""",
              (netflowid,))

    netflow = c.fetchone()

    if (netflow['is_malicious']):
        # check to make sure they didn't already guess this session
        c.execute("""select count(id) as count from team_guesses where team_id = %s and service_id = %s and session = %s""",
                  (teamid, netflow['service_id'], netflow['session']))
        count = c.fetchone()['count']
        if count != 0:
            result['result'] = 'error'
            result['reason'] = "You already correctly identified that series of netflows as malicious"
            return json.dumps(result)

    created_timestamp = iso8601.parse_date(netflow['created_timestamp'])
    current_timestamp = iso8601.parse_date(datetime.datetime.now().isoformat())
    result = {}

    if netflow['team_id'] != int(teamid):
        result['result'] = 'error'
        result['reason'] = "That's not your netflow!"
    elif netflow['is_malicious']:
        # if it is, give them some amount of positive points
        result['result'] = "correct"

        c.execute("""insert into team_guesses (team_id, netflow_id, session, service_id, is_correct, created_on) values (%s, %s, %s, %s, 1, %s)""",
                  (teamid, netflowid, netflow['session'], netflow['service_id'], datetime.datetime.now().isoformat()))

        c.execute("""update netflows set marked_status = 'correct' where id = %s limit 1""",
                  (netflowid,))
    else:
        # if it isn't, give them a smaller amount of negative points
        result['result'] = "incorrect"

        c.execute("""insert into team_guesses (team_id, netflow_id, session, service_id, is_correct, created_on) values (%s, %s, %s, %s, 0, %s)""",
                  (teamid, netflowid, netflow['session'], netflow['service_id'], datetime.datetime.now().isoformat()))

        c.execute("""update netflows set marked_status = 'incorrect' where id = %s limit 1""",
                  (netflowid,))

    mysql.get_db().commit()
    return json.dumps(result)

# exploit stuff

@app.route("/submitscript/<teamid>/<serviceid>", methods=['POST'])
def submit_script(teamid, serviceid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    script = request.form.get('script')
    name = request.form.get('name')
    type = request.form.get('type')

    c = mysql.get_db().cursor()
    
    c.execute("""insert into scripts (name, is_ours, type, team_id, service_id, created_on, latest_script)
                 values (%s, 1, %s, %s, %s, %s, 1)""",
              (name, type, teamid, serviceid, datetime.datetime.now().isoformat()))              

    result = {"id" : mysql.get_db().insert_id()}

    c.execute("""insert into script_payload (script_id, payload, created_on) values (%s, %s, %s)""",
              (result['id'], script, datetime.datetime.now().isoformat()))

    mysql.get_db().commit()
    return json.dumps(result)

@app.route("/updatescript/<scriptid>", methods=['POST'])
def update_script(scriptid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    script = request.form.get('script')

    c = mysql.get_db().cursor()

    test_decode = base64.b64decode(script)
    c.execute("""insert into script_payload (script_id, payload, created_on) values (%s, %s, %s)""",
              (scriptid, script, datetime.datetime.now().isoformat()))

    mysql.get_db().commit()
    return json.dumps({'result': "great success"})
    
        

@app.route("/submitexploit/<teamid>/<serviceid>", methods=['POST'])
def submit_exploit(teamid, serviceid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    exploit = request.form.get('exploit')
    name = request.form.get('name')
    is_bundle = int(request.form.get('is_bundle'))

    c = mysql.get_db().cursor()

    c.execute("""update scripts set latest_script = 0 where team_id = %s and service_id = %s""",
              (teamid, serviceid))

    c.execute("""insert into scripts (is_ours, type, team_id, service_id, name, latest_script, is_bundle, created_on) 
                 values (0, 'exploit', %s, %s, %s, 1, %s, %s)""",
              (teamid, serviceid, name, is_bundle, datetime.datetime.now().isoformat()))

    result = {"id" : mysql.get_db().insert_id()}

    test_decode = base64.b64decode(exploit)
    c.execute("""insert into script_payload (script_id, payload, created_on) values (%s, %s, %s)""",
              (result['id'], exploit, datetime.datetime.now().isoformat()))


    mysql.get_db().commit()
    return json.dumps(result)

@app.route("/allscripts")
def all_scripts():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select id, name, type, is_ours, is_bundle, feedback, team_id, service_id, is_working, latest_script from scripts""")

    result = {'scripts' : c.fetchall()}
    return json.dumps(result)

@app.route("/allscripts/<thetype>")
def all_scripts_limited(thetype):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select id, name, type, is_ours, is_bundle, feedback, service_id, latest_script from scripts where type = %s""",
              (thetype,))

    result = {'scripts' : c.fetchall()}
    return json.dumps(result)


@app.route("/workingexploits")
def get_all_working_exploits():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    
    c.execute("""select id, is_ours, is_bundle, type, team_id, service_id, is_working, name, latest_script from scripts where (is_working = 1 or is_ours = 1) and type = 'exploit'""")

    result = {'scripts' : c.fetchall()}
    return json.dumps(result)
        

@app.route("/script/<scriptid>")
def get_script(scriptid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select id, name, type, is_ours, is_bundle, feedback, team_id, service_id, is_working, latest_script from scripts where id = %s limit 1""",
              (scriptid,))

    script = c.fetchone()

    c.execute("""select payload from script_payload where script_id = %s order by created_on desc limit 1""",
              (scriptid,))
    payload = c.fetchone()
    
    
    script.update({'payload' : payload['payload']})

    return json.dumps(script)

# @app.route("/setcallinterval/<scriptid>")
# def set_call_interval(scriptid):
#     secret = request.args.get('secret')

#     if secret != "YOUKNOWSOMETHINGYOUSUCK":
#         abort(401)

#     call_interval = int(request.args.get('call_interval'))
#     call_interval_sd = float(request.args.get('call_interval_sd'))

#     c = mysql.get_db().cursor()
    
#     c.execute("""update scripts set call_interval = %s, call_interval_sd = %s where id = %s""",
#               (call_interval, call_interval_sd, scriptid))

#     mysql.get_db().commit()

#     return json.dumps({'result' : 'great success'})
        


@app.route("/ranscript/<scriptid>")
def ran_script(scriptid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    defending_team = request.args.get('team_id')
    error = int(request.args.get('error'))
    error_msg = request.args.get('error_msg')
    
    c = mysql.get_db().cursor()

    c.execute("""select is_ours, type, team_id, service_id from scripts where id = %s limit 1""",
              (scriptid,))
    
    script = c.fetchone()

    if script['type'] == "exploit":
        c.execute("""insert into exploit_attacks (script_id, service_id, attacking_team_id, defending_team_id, is_attack_success, created_on) values (%s, %s, %s, %s, %s, %s)""",
                  (scriptid, script['service_id'], script['team_id'], defending_team, int(error == 0), datetime.datetime.now().isoformat()))


    c.execute("""insert into script_runs (script_id, defending_team_id, error, error_msg, created_on) values (%s, %s, %s, %s, %s)""",
              (scriptid, defending_team, error, error_msg, datetime.datetime.now().isoformat()))

    mysql.get_db().commit()

    return json.dumps({'result' : 'great success'})




@app.route("/ranexploit/<scriptid>")
def exploit_was_run(scriptid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    defending_team = request.args.get('defending_team')
    is_attack_successful = int(request.args.get('is_attack_success'))

    if not (is_attack_successful == 1 or is_attack_successful == 0):
        abort(400)

    c = mysql.get_db().cursor()

    # check that defending team ID is legit
    c.execute("""select count(id) as count from teams where id = %s""",
              (defending_team,))

    count = c.fetchone()['count']
    if count == 0:
        return json.dumps({'result': 'error', 'reason': "I don't know that defending team"})

    c.execute("""select is_ours, type, team_id from scripts where id = %s limit 1""",
              (scriptid,))
    
    script = c.fetchone()

    if script['type'] != "exploit":
        abort(400)

    if script['is_ours'] == False and is_attack_successful:
        # Give them some points!
        points = points_successful_exploitation()        
        c.execute("""insert into team_score (team_id, score, reason, type, created_on) values (%s, %s, %s, %s, %s)""",
                  (script['team_id'], points, "successfully exploited team " + defending_team, 'attack', datetime.datetime.now().isoformat()))



    c.execute("""insert into exploit_attacks (script_id, defending_team_id, is_attack_success, created_on) values (%s, %s, %s, %s)""",
              (scriptid, defending_team, is_attack_successful, datetime.datetime.now().isoformat()))

    mysql.get_db().commit()

    return json.dumps({'result': 'great success'})

@app.route("/scriptresults/<scriptid>")
def get_script_results(scriptid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()    

    c.execute("""select type from scripts where id = %s limit 1""",
              (scriptid,))

    script_type = c.fetchone()['type']
    result = []
    if script_type == 'exploit':
        # fetch data from exploit table
        c.execute("""select id, defending_team_id, is_attack_success, created_on from exploit_attacks where script_id = %s order by created_on desc limit 200""",
                  (scriptid,))
        for run in c.fetchall():
            result.append({'id' : run['id'],
                           'defending_team_id' : run['defending_team_id'],
                           'error' : 0,
                           'error_msg' : "exploit successful" if run['is_attack_success'] == 1 else "exploit unsuccessful"})
        
    else:
        # fetch data from the scripts table
        c.execute("""select id, defending_team_id, error, error_msg, created_on from script_runs where script_id = %s order by created_on desc limit 200""",
                  (scriptid,))
        result = c.fetchall()                  

    return json.dumps({'runs' : result})
            


@app.route("/nontestedexploits")
def get_nontested_exploits():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()    
    c.execute("""select id, name, type, is_ours, is_bundle, team_id, service_id from scripts where is_working is NULL and type = 'exploit'""")

    result = {'exploits' : c.fetchall()}
    return json.dumps(result)

@app.route("/exploitworkingstatus/<exploitid>", methods=['POST'])
def set_exploit_working_status(exploitid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    is_working = request.form.get('is_working')
    feedback = request.form.get('feedback')

    c = mysql.get_db().cursor()
    
    c.execute("""update scripts set is_working = %s, feedback = %s where id = %s""",
              (is_working, feedback, exploitid))

    mysql.get_db().commit()

    return json.dumps({'result': 'great success'})



# flag stuff

@app.route("/newflag/<teamid>/<serviceid>")
def create_new_flag(teamid, serviceid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    flag = generate_new_flag()

    c.execute("""insert into flags (team_id, service_id, flag, created_on) values (%s, %s, %s, %s)""",
              (teamid, serviceid, flag, datetime.datetime.now().isoformat()))
    
    result = {'flag': flag}

    mysql.get_db().commit()

    return json.dumps(result)

@app.route("/setcookieandflagid/<flag>")
def set_cookie_and_flag_id(flag):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    cookie = request.args.get('cookie')
    flag_id = request.args.get('flag_id')

    c = mysql.get_db().cursor()

    c.execute("""update flags set flag_id = %s, cookie = %s where flag = %s""",
              (flag_id, cookie, flag))

    mysql.get_db().commit()

    return json.dumps({'result': "great success"})

@app.route("/getlatestflagandcookie/<teamid>/<serviceid>")
def get_latest_flag_and_cookie(teamid, serviceid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()    

    c.execute("""select flag, cookie, flag_id from flags where team_id = %s and service_id = %s order by created_on desc limit 1""",
              (teamid, serviceid))

    return json.dumps(c.fetchone())


@app.route("/scorethroughtime")
def get_score_through_time():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    c.execute("""select id, team_name as name, team_country as country, team_address as address, university_name as university from teams""")
    teams = c.fetchall()

    result = {}

    result['teams'] = []
    for team in teams:
        team_id = team['id']
        team_result = {}
        team_result.update(team)

        # get the uptime
        team_result['uptime'] = get_uptime_for_team(team_id, c)

        team_result['score_through_time'] = get_team_score_through_time(team_id, team_result['uptime'], c)
        result['teams'].append(team_result)

    return json.dumps(result)


@app.route("/scoreboard")
def get_scoreboard():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    result = {}

    result['teams'] = []
    
    c.execute("""select id, team_name as name, team_country as country, team_address as address, university_name as university from teams""")
    teams = c.fetchall()

    total_attack_points = get_total_points('attack', c)
    total_defense_points = get_total_points('defense', c)

    if total_attack_points == 0:
        total_attack_points = 1
    if total_defense_points == 0:
        total_defense_points = 1

    for team in teams:
        team_id = team['id']
        team_result = {}
        team_result.update(team)

        # get the uptime
        team_result['uptime'] = get_uptime_for_team(team_id, c)

        # get the score

        score = get_score_for_team(total_attack_points, total_defense_points, team_id, c)

        team_result['score'] = "{0:.2f}".format(score['score'] * (team_result['uptime'] / 100.0))
        team_result['attack_score'] = score['attack_score']
        team_result['defense_score'] = score['defense_score']


        # get the services and up/down status

        team_result['services'] = get_service_state(team_id, c)
        
        # get attacks false positives
        # get attacks false negatives
        # get attacks true negatives
        # get attacks true positives

        attack_statistics = get_attack_statistics(team_id, c)
        team_result.update(attack_statistics)

        # get counter attacks successful
        # get counter attacks total
        # get counter attacks detected
        counter_statistics = get_counter_attack_statistics(team_id, c)
        team_result.update(counter_statistics)

        # get team's score throughout time

        result['teams'].append(team_result)

    result['team_on_team_action'] = get_team_on_team_action(10, c)
        
    return json.dumps(result)

@app.route("/merch")
def get_all_merch():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    c.execute("""select id, name, description, min_bid, num_winners, max_wins, extra_info from merch""")
    return json.dumps({ 'merch' : c.fetchall()})

@app.route("/tickmerch/<tickid>")
def get_tick_merch(tickid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    
    merch_extra_info = {}
    c.execute("""select id, extra_info from merch""")
    for result in c.fetchall():
        merch_extra_info[result['id']] = result['extra_info']
    

    tick_info = []
    c.execute("""select team_id, merch_id, bid, is_successful, message, extra_info from team_merch_bids where tick_id = %s""",
              (tickid,))

    for result in c.fetchall():
        merch_id = result['merch_id']
        the_extra_info = merch_extra_info[merch_id]

        bid_extra_info = result['extra_info']
        merch_extra_info_parsed = None
        if the_extra_info == "exploit":
            c.execute("""select name from services where id = %s""",
                      (int(bid_extra_info),))

            merch_extra_info_parsed = c.fetchone()['name']
        elif the_extra_info == "team":
            c.execute("""select team_name as name from teams where id = %s""",
                      (int(bid_extra_info),))
            merch_extra_info_parsed = c.fetchone()['name']

        result['extra_info_parsed'] = merch_extra_info_parsed

        tick_info.append(result)
        
    return json.dumps({ 'tick_info' : tick_info})


@app.route("/teammerch")
def get_all_teams_merch():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    c.execute("""select team_id, SUM(credits) as total_credits from team_credits group by team_id""")
    
    teams_merch = []

    for result in c.fetchall():
        team_id = result['team_id']
        credits = int(result['total_credits'])

        c.execute("""select merch_id, COUNT(id) as count from team_merch_bids where team_id = %s and is_successful = 1 group by merch_id""",
                  (team_id,))

        num_wins = []
        for bids in c.fetchall():
            merch_id = bids['merch_id']
            wins = bids['count']
            num_wins.append({'merch_id' : merch_id, 'wins': wins})

        teams_merch.append({'team_id': team_id, 'num_wins' : num_wins, 'credits': credits})

    
    return json.dumps({ 'teams_merch' : teams_merch})

@app.route("/get_won_merch/<team_id>")
def get_merch_won(team_id):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select the_result from team_merch_results where team_id = %s and merch_id = 2""",
              (team_id,))

    exploits = []
    for exploit in c.fetchall():
        exploits.append(exploit['the_result'])

    c.execute("""select the_result from team_merch_results where team_id = %s and merch_id = 3""",
              (team_id,))

    attack_netflows = []
    for attack_netflow in c.fetchall():
        attack_netflows.append(attack_netflow['the_result'])
        
    
    
    return json.dumps({ 'exploits' : exploits, 'attack_netflows' : attack_netflows})


@app.route("/levels")
def get_all_levels():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()
    c.execute("""select id, name from levels""")
    levels = []
    for result in c.fetchall():
        level_id = result['id']
        level_name = result['name']

        level_limit = get_level_limit(level_id, c)
        
        c.execute("""select id, name, the_order from level_nodes where level_id = %s order by the_order""",
                  (level_id,))
        nodes = {}
        for node in c.fetchall():
            nodes[node['id']] = (node['the_order'], node['name'])

        c.execute("""select id, name from services""")
        services = []
        for service in c.fetchall():
            service_id = service['id']
            name = service['name']
        
            c.execute("""select node_id from node_service where service_id = %s""",
                      (service_id,))

            services_nodes = []
            for associated_node in c.fetchall():
                node_id = associated_node['node_id']
                if node_id in nodes:
                    services_nodes.append(nodes[node_id][1])
            if services_nodes:
                services.append({ 'service_id' : service_id, 'name': name, 'nodes': services_nodes})
        
        node_tuples_sorted = nodes.values()
        node_tuples_sorted.sort()
        levels.append({'level_id' : level_id, 'level_name': level_name, 'level_resources': level_limit, 'nodes': [n[1] for n in node_tuples_sorted], 'services': services})
    
    return json.dumps({ 'levels' : levels})

def get_level_limit(network_id, c):
    c.execute("""select score_limit from level_score_limit where level_id = %s order by created_on desc limit 1""",
              (network_id,))
    result = c.fetchone()
    return result['score_limit']


@app.route("/levelstate")
def get_levels_state():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    current_tick, time_left = get_current_tick(c)
    level_states = get_level_state(current_tick, c)
    return json.dumps({ 'level_state' : level_states})

@app.route("/levelstate/<tickid>")
def get_specific_tick_level_state(tickid):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    level_states = get_level_state(tickid, c)
    return json.dumps({ 'level_state' : level_states})


def get_level_state(tick_id, c):
    team_id_level = get_team_id_level(c)

    level_team_ids = {}
    for team_id, level_id in team_id_level.iteritems():
        if not level_id in level_team_ids: 
            level_team_ids[level_id] = []
        
        # Get the team's credits and resources _at_ this tick
        credits = get_team_credits(team_id, tick_id,  c)
        resources = get_team_resources(team_id, tick_id, level_id, c)
        level_team_ids[level_id].append({"team_id" : team_id, "resources": resources, "credits": credits})


    c.execute("""select id from levels""")

    level_states = []
    for result in c.fetchall():
        level_id = result['id']
        teams_at_level = level_team_ids.get(level_id, [])

        c.execute("""select active_state from level_active_state where level_id = %s and tick_id = %s order by created_on desc limit 1""",
                  (level_id, tick_id))
        result = c.fetchone()

        active_state = None
        if result:
            active_state = result['active_state']

        is_waiting = 0
        if len(teams_at_level) > 0 and active_state == None:
            is_waiting = 1

        level_states.append({'level_id' : level_id, 'is_waiting': is_waiting, 'active_node': active_state, 'teams': teams_at_level})

        

    return level_states

def get_team_credits(team_id, tick_id, c):
    credits = 0

    c.execute("""select created_on from ticks where id = %s""",
              (tick_id,))

    tick_created = c.fetchone()['created_on']

    c.execute("""select SUM(credits) as total_credits from team_credits where team_id = %s and created_on < %s""",
              (team_id, tick_created))

    return int(c.fetchone()['total_credits'])

def get_team_resources(team_id, tick_id, level_id, c):

    c.execute("""select created_on from ticks where id = %s""",
              (tick_id,))

    tick_created = c.fetchone()['created_on']

    c.execute("""select SUM(score) as total_resources from team_score where team_id = %s and level_id = %s and created_on < %s""",
              (team_id, level_id, tick_created))

    return int(c.fetchone()['total_resources'])

    

def get_total_points(type, c):
    c.execute("""select SUM(score) as sum from team_score where type = %s and id != 129""",
              (type,))
    result = c.fetchone()
    return float(result['sum'])

def get_score_for_team(total_attack_points, total_defense_points, team_id, c):
    c.execute("""select SUM(score) as sum from team_score where team_id = %s and type = 'attack'""",
              (team_id,))
    raw_attack = float(c.fetchone()['sum'])

    c.execute("""select SUM(score) as sum from team_score where team_id = %s and type = 'defense'""",
              (team_id,))

    raw_defense = float(c.fetchone()['sum'])

    result = {}

    result['attack_score'] = ((raw_attack * 1.0) / total_attack_points) * 100.0
    result['defense_score'] = ((raw_defense * 1.0) / total_defense_points) * 100.0

    result['score'] = (result['attack_score'] + result['defense_score']) / 2.0
    
    
    return result

def get_team_score_through_time(team_id, uptime, c):
    uptime_as_float = uptime / 100.0
    c.execute("""select score, created_on from team_score where team_id = %s order by created_on asc""",
              (team_id,))
    results = []
    current_points = 0.0
    for result in c.fetchall():
        this_score = result['score'] 
        points_now = current_points + this_score
        current_points = points_now
        
        points_to_show = points_now * uptime_as_float
        
        date = iso8601.parse_date(result['created_on'])

        unix_milliseconds = time.mktime(date.timetuple())*1e3 + date.microsecond/1e3
        
        results.append({'points_at_time' : points_to_show, 'timestamp': unix_milliseconds})

    return results
    
        

def get_team_on_team_action(timeframe, c):
    # timeframe is in minutes before here

    last_time = datetime.datetime.now() - datetime.timedelta(minutes=timeframe)

    c.execute("""select exploit_attacks.defending_team_id as defending_team, scripts.team_id as attacking_team from exploit_attacks, scripts where scripts.id = exploit_attacks.script_id and exploit_attacks.is_attack_success = 1 and scripts.team_id is not null and exploit_attacks.created_on > %s""",
              (last_time.isoformat(),))

    count = {}
    for attack in c.fetchall():
        key = (attack['attacking_team'], attack['defending_team'])
        if not key in count:
            count[key] = 0
        count[key] += 1

    result = []
    for key in count:
        result.append({'attacking_team': key[0], 'defending_team': key[1], 'magnitude': count[key]})

    return result

def get_service_state(team_id, c):
    c.execute("""select id, name from services""");
    services = c.fetchall()

    result = {}
    for service in services:
        c.execute("""select state from team_service_state where team_id = %s and service_id = %s order by created_on desc limit 1""",
                  (team_id, service['id']))
        state = c.fetchone()
        result[service['name']] = state['state']

    return result

def get_uptime_for_team(team_id, c):

    c.execute("""select COUNT(id) as count, service_id from team_service_state where team_id = %s group by service_id""",
              (team_id,))

    total_counts = {}
    for result in c.fetchall():
        total_counts[result['service_id']] = result['count']

    c.execute("""select COUNT(id) as count, service_id from team_service_state where team_id = %s and state = 2 group by service_id""",
              (team_id,))
    
    up_counts = {}
    for result in c.fetchall():
        up_counts[result['service_id']] = result['count']

    uptimes = {}
    for service_id in total_counts.keys():
        total = total_counts[service_id]
        up = up_counts[service_id]
        uptime = ((up * 1.0) / (total * 1.0)) * 100

        uptimes[service_id] = uptime

    # now average all the uptimes

    total = 0
    for service_id in uptimes.keys():
        total += uptimes[service_id]

    return total / len(uptimes)


def get_attack_statistics(team_id, c):
    
    # # first get the total number of netflows
    # c.execute("""select COUNT(id) as count from netflows where team_id = %s""",
    #           (team_id,))
    # total_number_of_netflows = c.fetchone()['count']

    # # then then number of malicious netflow
    # c.execute("""select COUNT(id) as count from netflows where team_id = %s and is_malicious = 1""",
    #           (team_id,))
    
    # total_malicious_netflows = c.fetchone()['count']

    # then get the number that they guessed correctly

    c.execute("""select COUNT(id) as count from team_guesses where team_id = %s and is_correct = 1""",
              (team_id,))

    total_correct_guesses = c.fetchone()['count']

    # then get the number that they guessed incorrectly
    
    c.execute("""select COUNT(id) as count from team_guesses where team_id = %s and is_correct = 0""",
              (team_id,))
    
    total_incorrect_guesses = c.fetchone()['count']

    total_guesses = total_correct_guesses + total_incorrect_guesses
    

    false_positives = 0
    if total_guesses > 0:
        false_positives = ((total_incorrect_guesses * 1.0 ) / total_guesses) * 100.0

    true_positives = 0
    if total_guesses > 0:
        true_positives = ((total_correct_guesses * 1.0 ) / total_guesses) * 100.0

    return {'attacks_false_positives' : false_positives,
            'attacks_false_negatives' : 0,
            'attacks_true_negatives' : 0,
            'attacks_true_positives' : true_positives}

def get_counter_attack_statistics(team_id, c):

    c.execute("""select COUNT(exploit_attacks.id) as count from scripts, exploit_attacks where scripts.team_id = %s and exploit_attacks.script_id = scripts.id""",
              (team_id,))

    total_attacks_by_team = c.fetchone()['count']

    c.execute("""select COUNT(team_guesses.id) as count from team_guesses, netflows, scripts where team_guesses.netflow_id = netflows.id and netflows.script_id = scripts.id and team_guesses.is_correct = 1 and scripts.team_id = %s""",
              (team_id,))

    detected_attacks = c.fetchone()['count']

    c.execute("""select COUNT(exploit_attacks.id) as count from scripts, exploit_attacks where scripts.team_id = %s and exploit_attacks.script_id = scripts.id and is_attack_success = 1""",
              (team_id,))

    successful_attacks = c.fetchone()['count']

    return {'counter_attacks_successful' : successful_attacks,
            'counter_attacks_total' : total_attacks_by_team,
            'counter_attacks_detected' : detected_attacks}

FLAG_POSSIBILITIES = string.ascii_uppercase + string.digits + string.ascii_lowercase
def generate_new_flag():
    new_flag = ''.join(random.choice(FLAG_POSSIBILITIES) for x in range(13))
    return "FLG" + new_flag

def get_current_tick(c):
    c.execute("""select id, time_to_change, created_on from ticks order by created_on desc limit 1""")
    result = c.fetchone()
    current_tick = 0
    seconds_left = 1337
    if result:
        current_tick = result['id']
        current_time = iso8601.parse_date(datetime.datetime.now().isoformat())
        time_to_change = iso8601.parse_date(result['time_to_change'])
        
        seconds_left = (time_to_change - current_time).total_seconds()
        if seconds_left < 0:
            seconds_left = 0
        
    return current_tick, seconds_left

def get_team_id_level(c):
    c.execute("""select id, (select level_id from team_level where team_level.team_id = teams.id order by team_level.created_on desc limit 1) as team_level from teams""")
    to_return = {}

    for result in c.fetchall():
        to_return[result['id']] = result["team_level"]
        
    return to_return



if __name__ == "__main__":
    app.run(host='0.0.0.0')
