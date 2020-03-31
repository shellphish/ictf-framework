from . import mysql
from .utils import get_current_tick
from scoring_ictf import lru_cache_decorator


def not_for_live_tick(f):
    def wrapper(tick, *args, **kwargs):
        if not (kwargs.pop('ignore_not_live_check', False)):
            cursor = mysql.cursor()
            current_tick, _, _, _ = get_current_tick(cursor)
            if tick >= current_tick:
                raise ValueError(
                    "Calling {} for the currently running tick or a tick in the future will return inconsistent results! Tick requested: {}, current tick: {}".format(f, tick, current_tick))

        return f(tick, *args, **kwargs)
    return wrapper


def get_game_id():
    cursor = mysql.cursor()
    cursor.execute("SELECT id FROM game LIMIT 1")
    result = cursor.fetchone()
    if result is None:
        return None
    return result['id']


def get_team_map():
    if get_game_id() is None:
        return None

    cursor = mysql.cursor()

    teams = dict()
    cursor.execute("""SELECT id, name from teams""")
    for result in cursor.fetchall():
        teams[result["id"]] = result["name"]

    return teams


def enabled_service_map():
    if get_game_id() is None:
        return None

    cursor = mysql.cursor()

    cursor.execute("""SELECT id, name FROM services WHERE current_state = 'enabled' """)
    services = dict()
    for result in cursor.fetchall():
        services[result["id"]] = result["name"]

    return services


@lru_cache_decorator(5) # this keeps 15 minutes worth of data
@not_for_live_tick
def get_full_service_status_report(tick):
    cursor = mysql.cursor()
    query = '''
        SELECT ts.team_id as team_id, ts.service_id as service_id, ts.state as state
        FROM curr_team_service_state ts
        WHERE ts.tick_id = %s
        ORDER BY ts.tick_id, ts.team_id
    '''

    # Dict[tick_id, Dict[team_id, Dict[service_id: state]]]
    service_states = {}
    cursor.execute(query, (tick,))
    for r in cursor.fetchall():
        tid, sid, state = r['team_id'], r['service_id'], r['state']
        if tid not in service_states:
            service_states[tid] = dict()

        service_states[tid][sid] = state

    return service_states


@lru_cache_decorator(5)
@not_for_live_tick
def get_attack_report(tick):
    cursor = mysql.cursor()
    query = '''
        SELECT fs.team_id as attacker_id, fl.team_id as owner_id, fs.service_id as service_id, fs.flag_id as flag_id
        FROM flag_submissions as fs, flags as fl
        WHERE fs.tick_id = %s
          AND fs.result = 'correct'
          AND fs.flag_id = fl.id
    '''

    cursor.execute(query, (tick,))
    out = {}
    for r in cursor.fetchall():
        att_id, own_id, sid, flag_id = r['attacker_id'], r['owner_id'], r['service_id'], r['flag_id']

        if sid not in out:
            out[sid] = dict()

        if own_id not in out[sid]:
            out[sid][own_id] = dict()

        out[sid][own_id][att_id] = flag_id

    return out


@not_for_live_tick
def get_scored_events(tick):
    service_status_report = get_full_service_status_report(tick, ignore_not_live_check=True)
    attack_info = get_attack_report(tick, ignore_not_live_check=True)
    final = {
            'service_status_report': service_status_report,
            'attack_report': attack_info,
    }
    return final


def submit_flag(team_id, flag, attack_up, max_incorrect_flags_per_tick, num_ticks_valid, attackup_head_bucket_size):
    cursor = mysql.cursor()

    # Check if the flag has been submitted by this team already.
    cursor.execute("""SELECT id, result FROM flag_submissions
                          WHERE team_id = %s AND flag = %s LIMIT 1""",
                   (team_id, flag))

    result = cursor.fetchone()
    if result:
        # We will return this also for 'ownflags' that are submitted twice.
        return {"result": "alreadysubmitted:{}".format(result["result"]), "id":     result["id"]}

    current_tick_id, _, _, _ = get_current_tick(cursor)

    # check if the team has been spamming invalid flags
    cursor.execute("""SELECT count(id) as count FROM flag_submissions
                          WHERE team_id = %s and tick_id = %s and result = 'incorrect'""",
                   (team_id, current_tick_id))

    num_incorrect_submissions = cursor.fetchone()["count"]
    if num_incorrect_submissions > max_incorrect_flags_per_tick:
        return {"result": "toomanyincorrect", "id":     None}

    # check if its a valid flag
    cursor.execute("""SELECT id, service_id, team_id, tick_id FROM flags
                          WHERE flag = %s""", (flag,))

    to_return, flag_info = {}, cursor.fetchone()
    service_id = None
    flag_id = None

    # Flag exists in database (= valid flag)
    if flag_info:
        flag_id = flag_info["id"]
        service_id = flag_info["service_id"]
        submitted_team_id = flag_info["team_id"]
        submitted_tick_id = flag_info["tick_id"]

        # TODO this is not needed for most ctf's
        # check that the service is not the team's own
        cursor.execute("""SELECT team_id FROM services WHERE id=%s LIMIT 1""", (service_id,))
        service_team_id = cursor.fetchone()["team_id"]

        # Team submitted their own flag
        if submitted_team_id == int(team_id) or int(team_id) == int(service_team_id):
            # We cannot simply return here because we need to commit
            # the database transaction first!
            to_return = {"result": "ownflag", "id": None}

        # Check if flag is still active
        else:

            # FIXME flag should be valid for some period of time as well as a number of ticks
            # flag is active if it is from this tick or the previous tick
            if current_tick_id - submitted_tick_id < num_ticks_valid:
                to_return = {"result": "correct"}

            # Flag is not active (too old)
            else:
                to_return = {"result": "notactive"}

        # In attack-up mode, put an extra check
        if attack_up and \
                to_return.get('result', None) == 'correct':
            from scores import _scores_get
            top_n_teams = _scores_get(top_n=attackup_head_bucket_size)
            if int(team_id) in top_n_teams:
                if int(submitted_team_id) not in top_n_teams:
                    # Top N teams can always attack each other, but no one else
                    to_return = {"result": "placetoolow"}
            else:
                team_scores_above = _scores_get(base_team_id=int(team_id))
                if int(submitted_team_id) not in team_scores_above:
                    to_return = {"result": "placetoolow"}

    # Invalid flag
    else:
        to_return = {"result": "incorrect"}

    # Flag did not exist in submissions, insert it
    cursor.execute("""INSERT INTO flag_submissions (team_id, flag, tick_id, result, service_id, flag_id)
                          VALUES (%s, %s, %s, %s, %s, %s)""",
                   (team_id, flag, current_tick_id, to_return["result"], service_id, flag_id))
    submission_id = cursor.lastrowid

    to_return["id"] = submission_id
    mysql.database.commit()
    return to_return