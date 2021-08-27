import json

from flask import request, abort

from . import app, mysql
from .utils import requires_auth, get_current_tick


# @app.route("/general_ping")
@app.route("/game/ping")
def general_ping():
    return "lareneg"

# General
#
@app.route("/game/ison")
def game_is_on():
    """The ``/game/on`` endpoint does not require auth
       It looks for an entry in game table, which means the game has started

       It can be reached at
       ``/game/on``.

       :return: JSON containing game_id.
       """
    cursor = mysql.cursor()
    to_return = {}
    cursor.execute("SELECT id FROM game LIMIT 1")
    game_cursor = cursor.fetchone()
    if game_cursor is None:
        to_return["num"] = "621"
        to_return["msg"] = "No game is currently running..."
        return json.dumps(to_return)

    to_return["game_id"] = game_cursor["id"]
    return json.dumps(to_return)


@app.route("/state")
@app.route("/game/state")
@requires_auth
def game_get_state():
    """The ``/game/state`` endpoint requires authentication and expects no
    other arguments.

    It can be reached at ``/game/state?secret=<API_SECRET>``.

    It is used to retrieve the current state of the game.

    The JSON response looks like::

        {
          "state_id": int,
          "game_id": int,
          "services": [List of {"service_id": int,
                                "service_name": string,
                                "port": int}],
          "scripts": [List of {"script_id": int,
                               "upload_id": int,
                               "type": ("exploit", "benign", "getflag",
                                        "setflag"),
                               "script_name": string,
                               "service_id": int}]
          "run_scripts": [{"team_id": int (team_id to run scripts against),
                           "run_list": [Ordered list of int script_ids]}],
          "state_expire": int (approximate remaining seconds in this tick),
        }

    :return: a JSON dictionary providing information on the current state.
    """
    cursor = mysql.cursor()

    # Get basic information about the game, like tick info and services
    to_return = {}
    current_tick, tick_start, seconds_to_next_tick, _ = get_current_tick(cursor)
    to_return["state_id"] = current_tick
    to_return["state_expire"] = seconds_to_next_tick

    cursor.execute("SELECT id FROM game LIMIT 1")
    game_cursor = cursor.fetchone()
    if game_cursor is None:
        to_return["num"] = "621"
        to_return["msg"] = "No game is currently running..."
        return json.dumps(to_return)

    to_return["game_id"] = game_cursor["id"]

    cursor.execute("""SELECT services.id AS service_id,
                             services.name as service_name,
                             services.port as port,
                             current_state as state
                      FROM services""")
    to_return["services"] = cursor.fetchall()

    # Determine which scripts exists and which should be run
    cursor.execute("""SELECT id AS script_id, upload_id, filename AS script_name,
                             type, service_id,
                             current_state as state
                      FROM scripts""")
    to_return["scripts"] = cursor.fetchall()

    cursor.execute("""SELECT team_id, json_list_of_scripts_to_run AS json_list
                      FROM team_scripts_run_status
                      WHERE team_scripts_run_status.tick_id = %s""",
                   (current_tick,))
    run_scripts = []
    for team_scripts_to_run in cursor.fetchall():
        team_id = team_scripts_to_run["team_id"]
        run_list = json.loads(team_scripts_to_run["json_list"])
        run_scripts.append({"team_id": team_id,
                            "run_list": run_list})

    to_return["run_scripts"] = run_scripts
    return json.dumps(to_return)


#@app.route("/getgameinfo")
@app.route("/game/info")
@requires_auth
def game_get_info():
    """The ``/game/info`` endpoint requires authentication and expects no
    other arguments.

    It can be reached at ``/game/info?secret=<API_SECRET>``.

    It is used to retrieve the information about the game, like team and service
    information.

    The JSON response looks like::

        {
          "services": [List of {"service_id": int,
                                "service_name": string,
                                "port": int,
                                "flag_id_description": string,
                                "description": string,
                                "state": ("enabled", "disabled")}],
          "teams": [List of {"team_id": int,
                             "team_name": string,
                             "url": string,
                             "country": 2-digit country code according
                                        to ISO-3166-1, ZZ for unknown}]
        }

    :return: a JSON dictionary with a list of all teams and a list of all
             services, including auxiliary information.

    """
    cursor = mysql.cursor()
    cursor.execute("""SELECT id as team_id, name as team_name,
                             url, country FROM teams""")
    teams = cursor.fetchall()

    _, tick_start, _, _ = get_current_tick(cursor)
    cursor.execute("""SELECT id as service_id, name as service_name,
                             port, flag_id_description, description,
                             current_state as state
                      FROM services""")
    services = cursor.fetchall()

    return json.dumps({"teams": teams,
                       "services": services})


#@app.route("/currenttick")
@app.route("/game/tick/")
@requires_auth
def current_tick_num():
    """The ``/game/tick/`` endpoint requires authentication and expects no
    other arguments.

    It can be reached at ``/game/tick?secret=<API_SECRET>`` or at
    ``/game/tick?secret=<API_SECRET>``.

    It is used to retrieve the information about the current tick.

    The JSON response looks like::
    {"created_on": "2015-11-30 17:01:42",
     "approximate_seconds_left": 0,
     "tick_id": 47}

    :return: a JSON dictionary with information about the current tick.
    """
    cursor = mysql.cursor()
    tick_id, created_on, seconds_left, ends_on = get_current_tick(cursor)
    return json.dumps({"tick_id": tick_id,
                       "created_on": str(created_on),
                       "approximate_seconds_left": seconds_left,
                       "ends_on": str(ends_on)})


@app.route("/game/tick/config")
@requires_auth
def get_tick_config():
    """The ``/game/tick/config`` endpoint requires authentication and expects no
    other arguments.

    It can be reached at ``/game/tick/config?secret=<API_SECRET>``.

    It is used to retrieve the information about the tick configuration.

    The JSON response looks like::

        {
          "NO_BEN": <Max_Number_of_benign_scripts_per_tick>,
          "NO_EXP": <Max_Number_of_exploit_scripts_per_tick>,
          "NO_GET_FLAGS": <Max_Number_of_get_flag_scripts_per_tick>,
          "TICK_TIME": <Tick_time_in_seconds>
        }

    :return: a JSON directory with corresponding configuration values.
    """
    cursor = mysql.cursor()
    cursor.execute("""SELECT name, value FROM ticks_configuration""")
    tick_config = {"NO_BEN": 0, "NO_EXP": 0, "TICK_TIME": 180, "NO_GET_FLAGS": 1}
    for curr_row in cursor.fetchall():
        if curr_row["name"] == "NUMBER_OF_BENIGN_SCRIPTS":
            tick_config["NO_BEN"] = curr_row["value"]
        if curr_row["name"] == "NUMBER_OF_EXPLOIT_SCRIPTS":
            tick_config["NO_EXP"] = curr_row["value"]
        if curr_row["name"] == "TICK_TIME_IN_SECONDS":
            tick_config["TICK_TIME"] = curr_row["value"]
        if curr_row["name"] == "NUMBER_OF_GETFLAGS":
            tick_config["NO_GET_FLAGS"] = curr_row["value"]

    return json.dumps(tick_config)

@app.route("/game/delete")
@requires_auth
def delete_game():
    """The ``/game/delete`` endpoint requires authentication.
    This creates a row in the game table

    It can be reached at
    ``/game/delete?secret=<API_SECRET>``.

    :return: JSON containing the deleted id.
    """
    cursor = mysql.cursor()
    cursor.execute("""DELETE FROM game""")
    mysql.database.commit()
    response = dict()
    response["game_id"] = 1
    return json.dumps(response)

@app.route("/game/insert")
@requires_auth
def insert_game():
    """The ``/game/insert`` endpoint requires authentication.
    This creates a row in the game table

    It can be reached at
    ``/game/insert?secret=<API_SECRET>``.

    :return: JSON containing inserted game_id.
    """
    cursor = mysql.cursor()
    cursor.execute("""INSERT INTO game VALUES (1) """)
    mysql.database.commit()
    response = dict()
    response["game_id"] = cursor.lastrowid
    return json.dumps(response)

# @app.route("/update/tick", methods=["POST"])
@app.route("/game/tick/update", methods=["POST"])
@requires_auth
def update_tick_info():
    """The ``/game/tick/update`` endpoint requires authentication.
    This updates the ticks table with the provided tick info.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/game/tick/update?secret=<API_SECRET>``.

    It requires the following POST inputs:

    - time_to_change: ISO formatted datetime string
    - created on: ISO formatted datetime string

    :return: JSON containing latest tick id, corresponding to
            the insertion.
    """
    time_to_change = request.form.get("time_to_change")
    created_on = request.form.get("created_on")
    cursor = mysql.cursor()
    cursor.execute("""INSERT INTO ticks (time_to_change, created_on)
                          VALUES (%s, %s)""", (time_to_change, created_on,))
    mysql.database.commit()
    response = dict()
    response["tick_id"] = cursor.lastrowid
    return json.dumps(response)
