#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import request, abort

from . import app, mysql
from .utils import requires_auth, get_current_tick


@app.route("/services/ping")
def services_ping():
    return "secivres"


# Services
#
@app.route("/services")
@app.route("/services/team/<int:team_id>")
@requires_auth
def services_get(team_id=None):
    """The ``/services`` endpoint requires authentication and can
    optionally filter by team_id or upload_id. It fetches service information.

    It can be reached at ``/services?secret=<API_SECRET>`` or
    ``/services/team/<int:team_id>``

    The JSON response looks like::
        {"services":
            service_id: {"id": int,
                         "name": str,
                         "port": int,
                         "authors": str,
                         "description": str,
                         "flag_id_description": str,
                         "team_id": int,
                         "upload_id": int,
                         "state": ("enabled", "disabled")
                         }
        }

    :param int team_id: optional ID of the team whose services should be
                        fetched
    :return: a JSON dictionary of service data.
    """
    cursor = mysql.cursor()

    base_query = """SELECT id as service_id, name as service_name, authors,
                         port, flag_id_description, description, team_id,
                         upload_id, current_state as state
                      FROM services"""

    # Dynamically create the WHERE statement
    filters = dict()
    filters["team_id = %s"] = team_id

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

    response = {"services": {}}
    for curr_row in cursor.fetchall():
        service_id = curr_row["service_id"]
        response["services"][service_id] = curr_row

    return json.dumps(response)


@app.route("/services/uploadid/<int:upload_id>")
@requires_auth
def services_uploadid(upload_id):
    """The ``/services/uploadid/<int:upload_id>`` endpoint requires authentication and expects an
    ``upload_id`` or an optional ``service_id`` arguments. Returns all
    services with this upload_id.

    It can be reached at ``/services/uploadid/<int:upload_id>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
          "services" : [List of {"id" : int,
                                "name": string
                                "port": int
                                "upload_id": int,
                                "team_id": int or NULL (NULL if it's our
                                                        service),
        }

    :param int upload_id: optional ID of the service for which the services
                           should be fetched.
    :return: a JSON dictionary that contains all services that match the
             filter.
    """

    cursor = mysql.cursor()

    cursor.execute("""SELECT id, name, port, team_id, upload_id, current_state as state
                      FROM services
                      WHERE upload_id = %s""",
                   (upload_id,))

    return json.dumps({"services": cursor.fetchall()})


@app.route("/services/state/enabled")
@requires_auth
def services_state_enabled():
    """The ``/services/state/enabled`` endpoint requires authentication and takes no
    additional parameters.  It fetches service information for all enabled services,
    in order of creation.
    Note that this enpoint sorts the services in order of creation

    It can be reached at ``/services/state/enabled?secret=<API_SECRET>``.

    The JSON response is a list of service dictionaries sorted by creation time:
        [{"id": int,
          "name": str,
          "port": int,
          "authors": str,
          "description": str,
          "flag_id_description": str,
          "team_id":, int
          "upload_id":, int
          }]

    :return: a JSON list of service data.
    """

    cursor = mysql.cursor()

    cursor.execute("""SELECT id, name as service_name,
                             port, flag_id_description, description, team_id,
                             current_state, upload_id
                      FROM services
                      WHERE current_state = 'enabled' """)

    services = cursor.fetchall()
    return json.dumps(services)


@app.route("/service/new", methods=["POST"])
@requires_auth
def service_new():
    """The ``/service/new`` endpoint requires
    authentication. It adds a service to the database and initializes its state.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/service/new?secret=<API_SECRET>``.

    It requires the following inputs:

    - name, the name of the service.
    - upload_id, upload which has the payload.
    - description, the description of the service.
    - authors, optional
    - flag_id_description, description of the flag_id
    - state, enabled, disabled. Defaults to "enabled"

    The JSON response looks like::

        {
          "id" : int,
          "result": ("success", "failure")
        }

    :return: a JSON dictionary containing status information.
    """
    name = request.form.get("name")
    upload_id = request.form.get("upload_id")
    description = request.form.get("description")
    authors = request.form.get("authors", None)
    flag_id_description = request.form.get("flag_id_description")
    state = request.form.get("state", "enabled")

    if state not in ("enabled", "disabled"):
        abort(400)

    cursor = mysql.cursor()

    # get the team_id from the uploads
    cursor.execute("""SELECT team_id
                          FROM uploads WHERE id = %s LIMIT 1""",
                   (upload_id,))
    result = cursor.fetchone()
    team_id = result["team_id"]

    cursor.execute("""INSERT INTO services (name, upload_id, description, authors,
                                           flag_id_description, team_id, current_state)
                      VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                   (name, upload_id, description, authors, flag_id_description,
                    team_id, state))
    service_id = cursor.lastrowid

    # set the state in the log
    tick_id, _, _, _ = get_current_tick(cursor)
    cursor.execute("""INSERT INTO service_state (service_id, state, reason, tick_id)
                      VALUES (%s, %s, %s, %s)""",
                   (service_id, state, "initial state", tick_id))

    # set the port number to service_id + 10000
    cursor.execute("""UPDATE services SET port = %s
                      WHERE id = %s""",
                   (service_id+10000, service_id))

    mysql.database.commit()

    return json.dumps({"result": "success",
                       "id": service_id})
@app.route("/services/all/status")
@app.route("/services/status/<int:team_id>")
@requires_auth
def services_get_status(team_id=0):
    """The ``/services/status/team`` endpoint requires authentication and takes an
    ``team_id`` argument. It fetches the services' status for the specified
    team for the current tick .

    The JSON response looks like::

        {
        team_id: {
                  service_id: {
                               "service_name": string,
                               "service_state": ("up",
                                                 "notfunctional",
                                                 "down",
                                                 "untested")
                              }
                 }
        }

    :param int team_id: optional tick_id
    :return: a JSON dictionary that maps teams to service states.
    """
    cursor = mysql.cursor()

    tick_id, _, _, _ = get_current_tick(cursor)

    if team_id == 0:
        team_id = "ts.team_id"

    # now get the real results
    cursor.execute("""SELECT ts.service_id, ts.tick_id, ts.team_id, ts.state, svcs.port, svcs.name
                      FROM curr_team_service_state ts, services svcs
                      WHERE (ts.tick_id = %s OR ts.tick_id = %s) AND ts.team_id=%s AND svcs.id = ts.service_id 
                      ORDER BY ts.tick_id, svcs.port""",
                   (tick_id, (tick_id-1), team_id))

    # build the result dict
    out = dict()
    for result in cursor.fetchall():
        nm = result["name"][slice(-10, None)]

        name_val = "{:10}".format(nm) + " status:{:4}".format(result["state"]) + " Port:" + str(result["port"])
        if result["tick_id"] not in out:
            out[result["tick_id"]] = list()

        out[result["tick_id"]].append(name_val)

    return json.dumps(out)

@app.route("/services/history/status")
@app.route("/services/history/status/cnt/<int:history_cnt>")
@requires_auth
def services_get_history_status(history_cnt=10):
    """The ``/services/history/statius`` endpoint requires authentication.
    It fetches the services' status for the last 10 ticks and summarizes them in a json object.

    The JSON response looks like::

        {
        service_info: {
                  team_id: [ status1, status2, status3 ... ]

                 }
        }

    :return: a JSON dictionary that maps teams to service states.
    """
    cursor = mysql.cursor()

    tick_id, _, _, _ = get_current_tick(cursor)
    lower_tick_id = tick_id - history_cnt
    print("LOWER TICK ID {}".format(lower_tick_id))
    sql = """ SELECT ts.service_id, ts.tick_id, ts.team_id, ts.state, svcs.port, svcs.name
              FROM curr_team_service_state ts, services svcs
              WHERE (ts.tick_id >= %s ) AND svcs.id = ts.service_id 
              ORDER BY svcs.port, ts.tick_id"""
    print(sql %  (lower_tick_id))
    # now get the real results
    cursor.execute(sql, (lower_tick_id,))

    # build the result dict
    out = dict()
    for result in cursor.fetchall():
        nm = "{}:{}".format(result["name"], result["port"])
        nm = nm[slice(-15, None)]
        if nm not in     out:
            out[nm] = dict()

        team_id = "team{:5}".format(result["team_id"])
        if team_id not in out[nm]:
            out[nm][team_id] = ""

        if result["state"] == "up":
            out[nm][team_id] += "____ "
        else:
            status = result["state"][slice(-4,None)]
            out[nm][team_id] +=  "{:4} ".format(status)

    return json.dumps(out)


@app.route("/services/states")
@app.route("/services/states/tick/<int:tick_id>")
@requires_auth
def services_get_states(tick_id=None):
    """The ``/services/states`` endpoint requires authentication and takes an
    optional ``tick_id`` argument. It fetches the services' states for all
    teams for the current tick if no ``tick_id`` is provided, or for the
    specified ``tick_id`` otherwise.

    It can be reached at ``/services/states?secret=<API_SECRET>``.

    It can also be reached at
    ``/services/states/tick/<tick_id>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
        team_id: {
                  service_id: {
                               "service_name": string,
                               "service_state": ("up",
                                                 "notfunctional",
                                                 "down",
                                                 "untested")
                              }
                 }
        }

    :param int tick_id: optional tick_id
    :return: a JSON dictionary that maps teams to service states.
    """
    cursor = mysql.cursor()
    if tick_id is None:
        tick_id, _, _, _ = get_current_tick(cursor)
        if tick_id > 0:
            tick_id -= 1

    cursor.execute("""SELECT id, name FROM services WHERE current_state = 'enabled' """)
    services = dict()
    for result in cursor.fetchall():
        services[result["id"]] = result["name"]

    # start building the dict
    # we do this here since the table of service states might not have results if things weren't going well
    # in which case services are untested
    teams = dict()
    cursor.execute("""SELECT id from teams""")
    for result in cursor.fetchall():
        team_id = result["id"]
        teams[team_id] = dict()
        for service_id, name in services.items():
            teams[team_id][service_id] = {"service_name": name, "service_state": "untested"}

    # now get the real results
    cursor.execute("""SELECT ts.team_id, ts.service_id, ts.state, s.name
                          FROM curr_team_service_state as ts
                      JOIN services as s ON s.id = ts.service_id
                      WHERE tick_id = %s AND s.current_state = 'enabled' """,
                   (tick_id,))

    # build the result dict
    for result in cursor.fetchall():
        team_id = result["team_id"]
        service_name = result["name"]
        service_id = result["service_id"]
        state = result["state"]

        service_dict = dict()
        service_dict["service_name"] = service_name
        service_dict["service_state"] = state

        teams[team_id][service_id] = service_dict

    return json.dumps({"service_states": teams})


@app.route("/service/enable/<int:service_id>", methods=["POST"])
@app.route("/service/disable/<int:service_id>", methods=["POST"])
@requires_auth
def service_enable_disable(service_id):
    """The ``/service/enable`` and ``/service/disable`` endpoints requires
    authentication and expect no additional arguments. It enables or disables
    a service starting at the next tick.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/service/enable/<service_id>?secret=<API_SECRET>`` or
    ``/service/disable/<service_id>?secret=<API_SECRET>``.

    It expects the following inputs:

    - reason, the reason why the service was enabled (optional)

    The optional ``reason`` argument is any string and justifies why the the
    service was enabled or disabled.

    The JSON response is::

        {
          "id": int,
          "result": ("success", "failure")
        }

    :param int service_id: the id of the service to be enabled or disabled.
    :return: a JSON dictionary with a result status, to verify if setting the
             state was successful.
    """
    state = "enabled" if "enable" in request.path else "disabled"
    reason = request.form.get("reason", None)

    cursor = mysql.cursor()
    tick_id, _, _, _ = get_current_tick(cursor)

    cursor.execute("""UPDATE services set current_state = %s
                      WHERE id = %s""",
                   (state, service_id))

    # update the service_state log
    cursor.execute("""INSERT INTO service_state
                             (service_id, state, reason, tick_id)
                      VALUES (%s, %s, %s, %s)""",
                   (service_id, state, reason, tick_id))
    mysql.database.commit()

    return json.dumps({"id": cursor.lastrowid,
                       "result": "success"})


@app.route("/service/state/set/bulk", methods=["POST"])
@requires_auth
def service_set_state_bulk_mode():
    """The ``/service/state/set/bulk`` endpoint requires authentication.
    It sets the state for a given list of services to corresponding states.
    This is the bulk mode version of ``/service/state/set```

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/service/state/set/bulk?secret=<API_SECRET>``.

    It expects the following inputs:

    - "bulk_update_info", which is a json list containing service ids, team id, state, and reason
      in following format:
      [ {"team_id" : <team_id>,
        "service_id" : <service_id>,
        "state" : <new_state>,
        "tick_id" : <target_tick_id>,
        "reason" : <reason to change the state>}
      ]

    The JSON response is::

        {
          "result": ("success", "failure")
        }

    :return: a JSON dictionary with a result status, to verify if setting the
             state was successful.
    """
    bulk_info = request.form.get("bulk_update_info")
    enabled_services = []
    for curr_serv_info in json.loads(services_state_enabled()):
        enabled_services.append(str(curr_serv_info["id"]))
    bulk_info_json = json.loads(bulk_info)
    cursor = mysql.cursor()
    for curr_bulk_info in bulk_info_json:
        state = curr_bulk_info["state"]
        team_id = curr_bulk_info["team_id"]
        service_id = curr_bulk_info["service_id"]
        reason = curr_bulk_info["reason"]
        tick_id = int(curr_bulk_info["tick_id"])

        # Allow old numerical-style status and convert to enum
        if state not in ("up", "notfunctional", "down"):
            old_code = int(state)
            if old_code not in (0, 1, 2):
                abort(400)
            state = ["down", "notfunctional", "up"][int(state)]

        if state not in ("up", "notfunctional", "down"):
            abort(400)

        # check that the service is enabled, otherwise state is untested
        if str(service_id) not in enabled_services:
            state = "untested"

        # get the new state for the current state table
        cursor.execute("""SELECT state
                          FROM curr_team_service_state
                          WHERE tick_id = %s and team_id = %s and service_id = %s LIMIT 1""",
                          (tick_id, team_id, service_id))
        result = cursor.fetchone()
        new_state = state
        if result:
            # the new state for the current table will be down if it was down at all that tick
            if result["state"] == "down" or state == "down":
                new_state = "down"
            elif result["state"] == "notfunctional" or state == "notfunctional":
                new_state = "notfunctional"
            elif result["state"] == "up" or state == "up":
                new_state = "up"

        # add to the log
        cursor.execute("""INSERT INTO team_service_state
                                 (team_id, service_id, state, reason, tick_id)
                          VALUES (%s, %s, %s, %s, %s)""",
                       (team_id, service_id, state, reason, tick_id))

        # update the current state
        cursor.execute("""INSERT INTO curr_team_service_state
                              (tick_id, team_id, service_id, state)
                          VALUES(%s, %s, %s, %s)
                          ON DUPLICATE KEY UPDATE state=%s""",
                       (tick_id, team_id, service_id, new_state, new_state))

    mysql.database.commit()

    return json.dumps({"result": "success"})


@app.route("/service/state/set/<int:service_id>/team/<int:team_id>",
           methods=["POST"])
@requires_auth
def service_set_state(service_id, team_id):
    """The ``/service/state`` endpoint requires authentication and expects
    the ``team_id`` and ``service_id`` as additional arguments. It sets the
    the state for a specific service for a specific team.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/service/state/set/<service_id>/team/<team_id>?secret=<API_SECRET>``.

    It expects the following inputs:

    - state, the state the service is in.
    - reason, the reason why the state was changed.

    The ``state`` argument must conform to the following notion:

    - up, which means the service is up
    - notfunctional, which means it is up but not functional
    - down, which means it is down (refusing connections)

    The ``reason`` argument is any string and can be a return value of a
    verification script.

    The JSON response is::

        {
          "id": int,
          "result": ("success", "failure")
        }

    :param int team_id: the ID of the team to be updated.
    :param int service_id: the ID of the service to be updated.
    :return: a JSON dictionary with a result status, to verify if setting the
             state was successful.
    """
    state = request.form.get("state")
    reason = request.form.get("reason")

    # Allow old numerical-style status and convert to enum
    if state not in ("up", "notfunctional", "down"):
        old_code = int(state)
        if old_code not in (0, 1, 2):
            abort(400)
        state = ["down", "notfunctional", "up"][int(state)]

    if state not in ("up", "notfunctional", "down"):
        abort(400)

    cursor = mysql.cursor()
    tick_id, _, _, _ = get_current_tick(cursor)

    # check that the service is enabled, otherwise state is untested
    cursor.execute("""SELECT current_state
                         FROM services
                      WHERE id = %s LIMIT 1""",
                   (service_id,))
    result = cursor.fetchone()
    if result["current_state"] != 'enabled':
        state = "untested"

    # get the new state for the current state table
    cursor.execute("""SELECT state
                         FROM curr_team_service_state
                      WHERE tick_id = %s and team_id = %s and service_id = %s LIMIT 1""",
                   (tick_id, team_id, service_id))
    result = cursor.fetchone()
    new_state = state
    if result:
        # the new state for the current table will be down if it was down at all that tick
        if result["state"] == "down" or state == "down":
            new_state = "down"
        elif result["state"] == "notfunctional" or state == "notfunctional":
            new_state = "notfunctional"
        elif result["state"] == "up" or state == "up":
            new_state = "up"

    # add to the log
    cursor.execute("""INSERT INTO team_service_state
                             (team_id, service_id, state, reason, tick_id)
                      VALUES (%s, %s, %s, %s, %s)""",
                   (team_id, service_id, state, reason, tick_id))

    # update the current state
    cursor.execute("""INSERT INTO curr_team_service_state
                          (tick_id, team_id, service_id, state)
                      VALUES(%s, %s, %s, %s)
                      ON DUPLICATE KEY UPDATE state=%s""",
                   (tick_id, team_id, service_id, new_state, new_state))

    mysql.database.commit()

    return json.dumps({"id": cursor.lastrowid,
                       "result": "success"})


#@app.route("/exploitedservices")
@app.route("/services/exploited")
@requires_auth
def exploited_services():
    """The ``/services/exploited`` endpoint requires authentication and expects
    no additional argument. It is used to retrieve which services have been
    exploited by which team.

    It can be reached at ``/services/exploited?secret=<API_SECRET>``.

    The JSON response is::

        {
          "exploited_services": {service_id: { "service_name": string,
                                               "teams": [{team_name: string,
                                                        team_id: int}]
                                               "total_flags_stolen": int }}
        }

    :return: a JSON dictionary containing status infromation on the exploited
             services.
    """
    cursor = mysql.cursor()

    service_to_counts = dict()

    cursor.execute("""SELECT count(id) AS count, service_id
                      FROM flag_submissions
                      WHERE result='correct'
                      GROUP BY service_id""")
    for result in cursor.fetchall():
        service_to_counts[result["service_id"]] = result["count"]

    cursor.execute("""SELECT DISTINCT flag_submissions.team_id, service_id,
                                      teams.name AS team_name,
                                      services.name AS service_name
                      FROM flag_submissions
                      JOIN teams
                      JOIN services
                        ON flag_submissions.team_id = teams.id
                       AND flag_submissions.service_id = services.id
                      WHERE result = 'correct' """)

    result = {}
    for row in cursor.fetchall():
        team_id = row["team_id"]
        team_name = row["team_name"]
        service_id = row["service_id"]
        service_name = row["service_name"]
        if service_id not in result:
            result[service_id] = {}
            result[service_id]["total_flags_stolen"] = service_to_counts[service_id]
            result[service_id]["service_name"] = service_name
            result[service_id]["teams"] = []
        result[service_id]["teams"].append({"team_name": team_name,
                                            "team_id": team_id})
    return json.dumps({"exploited_services": result})


