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

POINTS_PER_CAP = 100


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
    c.execute("""select id as team_id, team_name, ip_range from teams""");
    result['teams'] = c.fetchall()

    c.execute("""select id as service_id, name as service_name, port, flag_id_description, description from services""");
    result['services'] = c.fetchall()

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
              (tick_id,))
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

@app.route("/allscripts")
def all_scripts():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select id, name, type, is_ours, is_bundle, feedback, team_id, service_id, is_working, latest_script from scripts""")

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
        abort(500)
        return


    c.execute("""insert into script_runs (script_id, defending_team_id, error, error_msg, created_on) values (%s, %s, %s, %s, %s)""",
              (scriptid, defending_team, error, error_msg, datetime.datetime.now().isoformat()))

    mysql.get_db().commit()

    return json.dumps({'result' : 'great success'})

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

    return result

@app.route("/getlatestflagids")
def get_latest_flag_ids():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()    

    flag_ids = {}

    c.execute("""select id from teams""")
    teams = []

    for result in c.fetchall():
        team_id = result['id']

        c.execute("""select id from services""")
        flag_ids[team_id] = {}
        for result in c.fetchall():
            service_id = result['id']

            c.execute("""select flag_id from flags where team_id = %s and service_id = %s order by created_on desc limit 1""",
                      (team_id, service_id))
            result = c.fetchone()
            if result:
                flag_id = result['flag_id']
                flag_ids[team_id][service_id] = flag_id
    

    to_return = { 'flag_ids' : flag_ids }
    return json.dumps(to_return)
    
@app.route("/submitflag/<teamid>/<flag>")
def submit_flag(teamid, flag):
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    # check if flag already submitted by this team

    c.execute("""select id from flag_submission where team_id = %s and flag = %s""",
              (teamid, flag))

    result = c.fetchone()
    if result:
        return json.dumps({'result': "alreadysubmitted", 'points': None})

    c.execute("""insert into flag_submission (team_id, flag, created_on) values (%s, %s, %s)""",
              (teamid, flag, datetime.datetime.now().isoformat()))


    c.execute("""select id, service_id, team_id from flags where flag = %s""",
              (flag,))

    to_return = {}

    result = c.fetchone()

    # valid flag
    if result:
        # check if the flag is the latest
        submitted_id = result['id']
        submitted_service = result['service_id']
        submitted_team_id = result['team_id']

        if submitted_team_id == int(teamid):
            to_return = {'result': 'ownflag', 'points': None}
        else:
            c.execute("""select id from flags where team_id = %s and service_id = %s order by created_on desc limit 1""",
                      (submitted_team_id, submitted_service))
            result = c.fetchone()
            latest_flag_id = result['id']

            if latest_flag_id == submitted_id:
                # Success! Give this team some points!
                points = POINTS_PER_CAP
                message = "Successfully captured active flag from service %s from team %s" % (submitted_service, submitted_team_id)
                c.execute("""insert into team_score (team_id, score, reason, created_on) values (%s, %s, %s, %s)""", 
                          (teamid, points, message, datetime.datetime.now().isoformat()))

                to_return = {'result': 'correct', 'points': points}

            else:
                to_return = {'result': 'notactive', 'points': None}

    else:
        to_return = {'result': 'incorrect', 'points': None}

    mysql.get_db().commit()
    return json.dumps(to_return)

@app.route("/scores")
def scores():
    secret = request.args.get('secret')

    if secret != "YOUKNOWSOMETHINGYOUSUCK":
        abort(401)

    c = mysql.get_db().cursor()

    c.execute("""select team_id, SUM(score) as score from team_score group by team_id""")

    to_return = { 'scores' : {}}
    for result in c.fetchall():
        team_id = result['team_id']
        team_result = {}
        team_result['raw_score'] = int(result['score'])

        sla_percentage = get_uptime_for_team(team_id, c)
        team_result['sla'] = int(sla_percentage)
        team_result['score'] = team_result['raw_score'] * (sla_percentage / 100.0)
        
        to_return['scores'][team_id] = team_result

    return json.dumps(to_return)



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

if __name__ == "__main__":
    app.run(host='127.0.0.1')
