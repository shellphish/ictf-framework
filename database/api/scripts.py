#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import request, abort

from . import app, mysql
from .utils import requires_auth, get_current_tick


@app.route("/scripts/ping")
def scripts_ping():
    return "stpircs"


# pylint:disable=redefined-builtin
#@app.route("/allscripts")
@app.route("/scripts")
@app.route("/scripts/service/<int:service_id>")
@app.route("/scripts/state/<state>")
@app.route("/scripts/team/<int:team_id>")
@app.route("/scripts/type/<type>")
@app.route("/scripts/service/<int:service_id>/state/<state>")
@app.route("/scripts/service/<int:service_id>/team/<int:team_id>")
@app.route("/scripts/service/<int:service_id>/type/<type>")
@app.route("/scripts/service/<int:service_id>/state/<state>"
           "/team/<int:team_id>")
@app.route("/scripts/service/<int:service_id>/state/<state>"
           "/team/<int:team_id>/type/<type>")
@app.route("/scripts/state/<state>/team/<int:team_id>")
@app.route("/scripts/state/<state>/team/<int:team_id>/type/<type>")
@app.route("/scripts/state/<state>/type/<type>")
@app.route("/scripts/team/<int:team_id>/type/<type>")
@requires_auth
def scripts(service_id=None, state=None, team_id=None, type=None):
    """The ``/scripts`` endpoint requires authentication and can take an
    optional ``team_id``, ``service_id``, ``state``, or ``type`` arguments. By default,
    it returns all scripts for all services.

    It can be reached at ``/scripts?secret=<API_SECRET>``.

    Additional server-side filtering is possible, by:

    - team
    - service
    - state
    - type

    For services, it can be reached at:

    - ``/scripts/service/<service_id>?secret=<API_SECRET>``.

    For teams, it can be reached at:

    - ``/scripts/team/<team_id>?secret=<API_SECRET>``.

    It can be further filtered down by ``type``.

    Filters are ordered alphabetically, that is: a ``service`` filter must occur
    before a ``team`` filter, and a ``team`` filter must occur before a
    ``type`` filter.

    - ``/scripts/type/<type>?secret=<API_SECRET>``,
    - ``/scripts/service/<service_id>/state/<state>?secret=<API_SECRET>``.
    - ``/scripts/team/<team_id>/type/<type>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
          "scripts" : [List of {"id" : int,
                                "type": ("exploit", "benign", "getflag",
                                         "setflag"),
                                "filename": string
                                "upload_id": int,
                                "team_id": int or NULL (NULL if it's our
                                                        exploit),
                                "service_id" : int,
                                "service_name" : string,
                                "state" : ("enabled", "disabled")}]
        }

    :param int service_id: optional ID of the service for which the scripts
                           should be fetched.
    :param str state: optional state for which the scripts should be fetched.
    :param int team_id: optional ID of the team whose scripts should be
                        fetched
    :param str type: optional type of the script that should be fetched.
    :return: a JSON dictionary that contains all scripts that match the
             filter.
    """
    if state is not None and state not in ("enabled", "disabled"):
        abort(400)

    cursor = mysql.cursor()

    base_query = """SELECT scripts.id as id, filename,
                           scripts.type as type, scripts.upload_id as upload_id, service_id,
                           services.name as service_name, scripts.team_id as team_id,
                           scripts.current_state as state
                    FROM scripts
                    JOIN services ON scripts.service_id = services.id"""

    # Dynamically create the WHERE statement
    filters = dict()
    filters["service_id = %s"] = service_id
    filters["state = %s"] = state
    filters["scripts.team_id = %s"] = team_id
    filters["type = %s"] = type

    # We cannot use a dict comprehension here with keys() and values() after
    # because their order is not guaranteed to be the same.
    filter_stmts, filter_values = [], []
    for stmt, value in filters.items():
        if value is not None:
            filter_stmts.append(stmt)
            filter_values.append(value)
    filter_stmt = " AND ".join(filter_stmts)
    filter_values = tuple(filter_values)

    if filter_stmt:
        cursor.execute("{} WHERE {}".format(base_query, filter_stmt),
                       filter_values)
    else:
        cursor.execute(base_query)

    return json.dumps({"scripts": cursor.fetchall()})
# pylint:enable=redefined-builtin


@app.route("/scripts/uploadid/<int:upload_id>")
@requires_auth
def scripts_uploadid(upload_id):
    """The ``/scripts/uploadid/<int:upload_id>`` endpoint requires authentication and expects an
    ``upload_id`` or an optional ``service_id`` arguments. Returns all
    scripts with this upload_id.

    It can be reached at ``/scripts/uploadid/<int:upload_id>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
          "scripts" : [List of {"id" : int,
                                "type": ("exploit", "benign", "getflag",
                                         "setflag"),
                                "filename": string
                                "upload_id": int,
                                "team_id": int or NULL (NULL if it's our
                                                        exploit),
                                "service_id" : int
        }

    :param int upload_id: optional ID of the service for which the scripts
                           should be fetched.
    :return: a JSON dictionary that contains all scripts that match the
             filter.
    """

    cursor = mysql.cursor()

    cursor.execute("""SELECT id, filename, type, upload_id, service_id, team_id
                      FROM scripts
                      WHERE upload_id = %s""",
                   (upload_id,))

    return json.dumps({"scripts": cursor.fetchall()})


@app.route("/scripts/get/torun")
@app.route("/scripts/get/torun/<int:tick_id>")
def get_scripts_to_run(tick_id=None):
    """
    The ``/scripts/get/torun`` endpoint requires authentication.
     By default, it returns all scripts that needs to be run for current tick.

    It can be reached at ``/scripts/get/torun?secret=<API_SECRET>``.

    The JSON response looks like::

        {
          "scripts_to_run" : [List of {
                                    "id" : int,
                                    "script_id" : int,
                                    "against_team_id": int,
                                    "tick_id" : int}]
        }

    :return: a JSON dictionary that contains all script that needs to be run.
    """
    cursor = mysql.cursor()

    # Get basic information about the game, like tick info and services
    if tick_id is None:
        current_tick, tick_start, seconds_to_next_tick, _ = get_current_tick(cursor)
        tick_id = current_tick

    cursor.execute("""SELECT id, script_id, against_team_id, tick_id
                      FROM script_runs
                      WHERE error is NULL AND tick_id = %s""",
                   (tick_id,))
    return json.dumps({"scripts_to_run": cursor.fetchall()})


@app.route("/scripts/runstats")
@app.route("/scripts/runstats/tick/<int:tick_id>")
@app.route("/scripts/runstats/tick/<int:tick_id>/team/<int:against_team_id>")
@app.route("/scripts/runstats/team/<int:against_team_id>")
def script_run_stats(against_team_id=None, tick_id=None):
    """The ``/scripts/runstats`` endpoint requires authentication and can take an
    optional ``team_id`` and an optional
    tick_id arguments. By default, it returns all scripts results for all
    teams for all ticks

    It can be reached at ``/scripts/runstats?secret=<API_SECRET>``.

    Additional server-side filtering is possible, by:

    - team
    - tick

    The JSON response looks like::

        {
          "script_runs" : [List of {"script_id" : int,
                                    "type": ("exploit", "benign", "getflag",
                                             "setflag"),
                                    "team_id": int or NULL (NULL if it's our
                                                            exploit)
                                    "service_id" : int,
                                    "service_name" : string,
                                    "number_successes" : int,
                                    "number_runs" : int,
                                    "not_ran" : int}]
        }

    :param int tick_id: optional ID of the tick to fetch scripts from
                        (defaults all ticks)
    :param int against_team_id: optional id of the team against whose the script runs should be
                        fetched.
    :return: a JSON dictionary that contains all script runs that match the
             filter.
    """
    cursor = mysql.cursor()

    base_query = """SELECT type,
                           CAST(SUM(CASE WHEN error = 0 THEN 1 ELSE 0 END)
                                AS SIGNED) AS successes,
                           COUNT(script_runs.id) AS number_runs,
                           CAST(SUM(CASE WHEN error IS NULL THEN 1 ELSE 0 END)
                                AS SIGNED) AS not_ran,
                           against_team_id, service_id, services.name as service_name
                    FROM script_runs
                    JOIN scripts
                    JOIN services
                      ON script_runs.script_id = scripts.id
                     AND scripts.service_id = services.id"""
    group_by = "GROUP BY service_id, against_team_id"

    # Dynamically create the WHERE statement
    filters = dict()
    filters["against_team_id = %s"] = against_team_id
    filters["script_runs.tick_id = %s"] = tick_id

    # We cannot use a dict comprehension here with keys() and values() after
    # because their order is not guaranteed to be the same.
    filter_stmts, filter_values = [], []
    for stmt, value in filters.items():
        if value is not None:
            filter_stmts.append(stmt)
            if type(value) == list:
                filter_values.extend(value)
            else:
                filter_values.append(value)
    filter_stmt = " AND ".join(filter_stmts)
    filter_values = tuple(filter_values)

    if filter_stmt:
        cursor.execute("{} WHERE {} {}".format(base_query, filter_stmt,
                                               group_by), filter_values)
    else:
        cursor.execute("{} {}".format(base_query, group_by))
    return json.dumps({"script_runs": cursor.fetchall()})




# @app.route("/scripts/runstats")
# @app.route("/scripts/runstats/tick/<int:tick_id>")
# @app.route("/scripts/runstats/tick/<int:tick_id>/team/<int:team_id>")
# @app.route("/scripts/runstats/team/<int:team_id>")
def script_run_stats_old_deprecated(team_id=None, tick_id=None):
    """The ``/scripts/runstats`` endpoint requires authentication and can take an
    optional ``team_id`` and an optional
    tick_id arguments. By default, it returns all scripts results for all
    teams for all ticks

    It can be reached at ``/scripts/runstats?secret=<API_SECRET>``.

    Additional server-side filtering is possible, by:

    - team
    - tick

    The JSON response looks like::

        {
          "script_runs" : [List of {"script_id" : int,
                                    "type": ("exploit", "benign", "getflag",
                                             "setflag"),
                                    "script_name": string,
                                    "team_id": int or NULL (NULL if it's our
                                                            exploit)
                                    "service_id" : int,
                                    "service_name" : string,
                                    "number_successes" : int,
                                    "number_runs" : int}]
        }

    :param int tick_id: optional ID of the tick to fetch scripts from
                        (defaults all ticks)
    :param int team_id: optional id of the team whose scripts should be
                        fetched.
    :return: a JSON dictionary that contains all script runs that match the
             filter.
    """
    cursor = mysql.cursor()

    base_query = """SELECT type,
                           CAST(SUM(CASE WHEN error = 0 THEN 1 ELSE 0 END)
                                AS SIGNED) AS successes,
                           COUNT(script_runs.id) AS number_runs,
                           scripts.team_id as team_id, script_id, service_id,
                           scripts.filename AS script_name
                    FROM script_runs
                    JOIN scripts
                    JOIN services
                      ON script_runs.script_id = scripts.id
                     AND scripts.service_id = services.id"""
    group_by = "GROUP BY script_id"

    # Dynamically create the WHERE statement
    filters = dict()
    filters["team_id = %s"] = team_id
    filters["script_runs.tick_id = %s"] = tick_id

    # We cannot use a dict comprehension here with keys() and values() after
    # because their order is not guaranteed to be the same.
    filter_stmts, filter_values = [], []
    for stmt, value in filters.items():
        if value is not None:
            filter_stmts.append(stmt)
            if type(value) == list:
                filter_values.extend(value)
            else:
                filter_values.append(value)
    filter_stmt = " AND ".join(filter_stmts)
    filter_values = tuple(filter_values)

    if filter_stmt:
        cursor.execute("{} WHERE {} {}".format(base_query, filter_stmt,
                                               group_by), filter_values)
    else:
        cursor.execute("{} {}".format(base_query, group_by))
    return json.dumps({"script_runs": cursor.fetchall()})


@app.route("/script/get/<int:script_id>")
@requires_auth
def script_get(script_id):
    """The ``/script/get/<script_id>`` endpoint requires authentication and
    expects the ``script_id`` as an additional argument. It returns
    information on this specific script, including its payload base64 encoded.

    It can be reached at ``/script/get/<script_id>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
          "id" : int,
          "type": ("exploit", "benign", "getflag", "setflag"),
          "team_id" : int or NULL (NULL if it's our exploit),
          "service_id" : int,
          "upload_id" : int,
          "filename": string,
          "state" : ("enabled", "disabled")
        }

    :return: a JSON dictionary that contains a specific scripts, including its
             payload (base64 encoded).
    """
    cursor = mysql.cursor()
    cursor.execute("""SELECT scripts.id, scripts.type, scripts.team_id,
                             scripts.service_id, scripts.upload_id, scripts.filename,
                             scripts.current_state as state,
                             uploads.payload
                      FROM scripts
                      JOIN uploads ON scripts.upload_id = uploads.id
                      WHERE scripts.id = %s LIMIT 1""", (script_id,))
    script = cursor.fetchone()
    script["payload"] = str(script["payload"])

    return json.dumps(script)


@app.route("/script/new", methods=["POST"])
@requires_auth
def script_new():
    """The ``/script/new`` endpoint requires authentication.
    It add a script to the database, and initializes its state.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/script/new?secret=<API_SECRET>``.

    It requires the following inputs:

    - name, an optional name of the script.
    - upload_id, upload which has the payload.
    - filename, the name of the file
    - type, the type of the script, currently exploit, benign, getflag, or
            setflag.
    - state, enabled, disabled. Defaults to "enabled"
    - service_id

    The JSON response looks like::

        {
          "id" : int,
          "result": ("success", "failure")
        }

    :return: a JSON dictionary containing status information.
    """
    upload_id = request.form.get("upload_id")
    filename = request.form.get("filename")
    type_ = request.form.get("type")
    state = request.form.get("state", "enabled")
    service_id = request.form.get("service_id")

    if state not in ("enabled", "disabled"):
        abort(400)

    cursor = mysql.cursor()

    # get the team_id from the uploads
    cursor.execute("""SELECT team_id
                          FROM uploads WHERE id = %s LIMIT 1""",
                   (upload_id,))
    result = cursor.fetchone()
    team_id = result["team_id"]


    # add the script
    cursor.execute("""INSERT INTO scripts (type, team_id, service_id,
                                           upload_id, filename, current_state)
                      VALUES (%s, %s, %s, %s, %s, %s)""",
                   (type_, team_id, service_id, upload_id,
                    filename, state))

    script_id = cursor.lastrowid

    # set it in the script state log
    tick_id, _, _, _ = get_current_tick(cursor)
    cursor.execute("""INSERT INTO script_state (script_id, state, reason, tick_id)
                      VALUES (%s, %s, %s, %s)""",
                   (script_id, state, "initial state", tick_id))
    mysql.database.commit()

    return json.dumps({"result": "success",
                       "id": script_id})


@app.route("/script/enable/<int:script_id>", methods=["POST"])
@app.route("/script/disable/<int:script_id>", methods=["POST"])
@requires_auth
def script_enable_disable(script_id):
    """The ``/script/enable`` and ``/script/disable`` endpoints requires
    authentication and expects the post parameter 'reason'. It enables or disables
    a script starting at the next tick. Reason describes why it was enabled/disabled

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/script/enable/<script_id>?secret=<API_SECRET>`` or
    ``/script/disable/<script_id>?secret=<API_SECRET>``.

    It expects the following inputs:

    - reason, the reason why the script was enabled (optional)

    The optional ``reason`` argument is any string and justifies why the the
    script was enabled or disabled.

    The JSON response is::

        {
          "id": int,
          "result": ("success", "failure")
        }

    :param int script_id: the id of the script to be enabled or disabled.
    :return: a JSON dictionary with a result status, to verify if setting the
             state was successful.
    """
    state = "enabled" if "enable" in request.path else "disabled"
    reason = request.form.get("reason", None)

    cursor = mysql.cursor()
    tick_id, _, _, _ = get_current_tick(cursor)
    cursor.execute("""UPDATE scripts set current_state = %s
                      WHERE id = %s""",
                   (state, script_id))

    # set it in the state log
    cursor.execute("""INSERT INTO script_state
                             (script_id, state, reason, tick_id)
                      VALUES (%s, %s, %s, %s)""",
                   (script_id, state, reason, tick_id))
    mysql.database.commit()

    return json.dumps({"id": cursor.lastrowid,
                       "result": "success"})


#@app.route("/ranscript/<int:script_id>", methods=["POST"])
@app.route("/script/ran/<int:script_run_id>", methods=["POST"])
@requires_auth
def script_ran(script_run_id):
    """The ``/script/ran/<script_run_id>`` endpoint requires authentication and
    expects the ``script_run_id`` as additional arguments. It is used to store the
    results of running script for a specific team.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/script/ran/<script_run_id>?secret=<API_SECRET>``.

    It requires the following POST inputs:

    - output, an output that might be displayed to players (optional).
    - error, a numeric error code (optional).
    - error_message, a possible error message (optional).

    The ``error message`` argument is any string and can be a return value of
    a verification script.

    The JSON response is::

        {
          "id": int
          "result": ("success", "failure")
        }

    :param int script_run_id: the script run ID (or execution ID) of the script that ran.
    :param str output: an optional script output.
    :param int error: the error code of the script
    :param str error_message: an optional error message.
    :return: a JSON dictionary with a result status and an identifier of the
             run (for debugging purposes), to verify if setting the state was
             successful.
    """
    output = request.form.get("output", None)
    error = int(request.form.get("error", 0))
    error_message = request.form.get("error_message", None)

    cursor = mysql.cursor()
    cursor.execute("""UPDATE script_runs
                      SET output = %s, error = %s, error_message = %s
                      WHERE id = %s""",
                   (output, error, error_message, script_run_id))
    mysql.database.commit()
    run_id = cursor.lastrowid

    return json.dumps({"id": run_id,
                       "result": "success"})


@app.route("/scripts/latest/enabled")
@requires_auth
def get_latest_enabled_scripts():
    """The ``/scripts/latest/enabled`` endpoint requires authentication.
    It is used to get latest enabled scripts for all services submitted
    by all teams including master/organizer where the team id will be
    Null.

    The JSON response is:
        {
          "scripts" : [List of {"id" : int,
                                "type": ("exploit", "benign", "getflag",
                                         "setflag"),
                                "team_id": int or NULL (NULL if it's our
                                                        exploit),
                                "service_id" : int}]
        }

    :return: a JSON dictionary that contains all latest working scripts.
    """

    cursor = mysql.cursor()
    # First, we need to get the latest scripts submitted by each team for each service.
    # Union that with all the scripts of administrator i.e get_flag/set_flag
    cursor.execute("""SELECT MAX(id) as id, type, team_id, service_id
                          FROM scripts
                          WHERE current_state = 'enabled'
                          AND team_id IS NOT NULL
                          GROUP BY team_id, service_id, type
                      UNION
                      SELECT id, type, team_id, service_id
                          FROM scripts
                          WHERE current_state = 'enabled'
                          AND team_id IS NULL
                          GROUP BY team_id, service_id, type""")

    return json.dumps({"scripts": cursor.fetchall()})


# @app.route("/update/torun/scripts/<int:team_id>", methods=["POST"])
@app.route("/scripts/torun/update/<int:team_id>", methods=["POST"])
@requires_auth
def update_scripts_to_run(team_id):
    """The ``/update/torun/scripts/<int:team_id>`` endpoint requires authentication and
    expects the ``team_id`` as additional arguments. It is used to store the
    scripts to run for each team for corresponding tick.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/update/torun/scripts/<int:team_id>?secret=<API_SECRET>``.

    It requires the following POST inputs:

    - tick_id, the tick id for which the scripts need to be scheduled.
    - scripts_in_json, json array containing list of scripts to run.

    The JSON response is::

        {
          "id": int
          "result": ("success", "failure")
        }

    :param int team_id: the ID of the team that the scripts need to be ran against.
    :return: a JSON dictionary with a result status and an identifier of the
             run (for debugging purposes), to verify if updating the scripts was
             successful.
    """
    tick_id = request.form.get("tick_id")
    json_scripts_to_run = request.form.get("scripts_in_json")
    scripts_list = json.loads(json_scripts_to_run)
    cursor = mysql.cursor()
    for curr_script_id in scripts_list:

        cursor.execute("""INSERT INTO script_runs
                                      (against_team_id, tick_id, script_id)
                          VALUES (%s, %s, %s)""", (team_id, tick_id, curr_script_id))

    mysql.database.commit()

    run_id = cursor.lastrowid

    return json.dumps({"id": run_id,
                       "result": "success"})


# @app.route("/update/torun/scripts/<int:team_id>", methods=["POST"])
# @app.route("/scripts/torun/update/<int:team_id>", methods=["POST"])
# @requires_auth
def update_scripts_to_run_old_deprecated(team_id):
    """The ``/update/torun/scripts/<int:team_id>`` endpoint requires authentication and
    expects the ``team_id`` as additional arguments. It is used to store the
    scripts to run for each team for corresponding tick.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/update/torun/scripts/<int:team_id>?secret=<API_SECRET>``.

    It requires the following POST inputs:

    - tick_id, the tick id for which the scripts need to be scheduled.
    - scripts_in_json, json array containing list of scripts to run.

    The JSON response is::

        {
          "id": int
          "result": ("success", "failure")
        }

    :param int team_id: the ID of the team that the scripts need to be ran against.
    :return: a JSON dictionary with a result status and an identifier of the
             run (for debugging purposes), to verify if updating the scripts was
             successful.
    """
    tick_id = request.form.get("tick_id")
    json_scripts_to_run = request.form.get("scripts_in_json")
    cursor = mysql.cursor()
    cursor.execute("""INSERT INTO team_scripts_run_status
                                     (team_id, tick_id,
                                      json_list_of_scripts_to_run)
                      VALUES (%s, %s, %s)""", (team_id, tick_id, json_scripts_to_run))

    mysql.database.commit()

    run_id = cursor.lastrowid

    return json.dumps({"id": run_id,
                       "result": "success"})


