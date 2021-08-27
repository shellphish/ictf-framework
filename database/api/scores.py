#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import json

from . import app, mysql
from .utils import requires_auth, get_current_tick
from .teams import teams_info
from flask import request


@app.route("/scores/ping")
def scores_ping():
    return "serocs"


# Scores

def _scores_get(tick_id=None, base_team_id=None, top_n=None):

    if base_team_id is not None and \
            not isinstance(base_team_id, (long, int)):
        raise TypeError("'base_team_id' can only be None or an int.")
    if top_n is not None and \
            not isinstance(top_n, (long, int)):
        raise TypeError("'top_n' can only be None or an int.")
    if base_team_id is not None and top_n is not None:
        raise ValueError("'base_team_id' and 'top_n' cannot be specified together.")

    cursor = mysql.cursor()
    if tick_id is None:
        cursor.execute("""SELECT MAX(tick_id) as max_tick from team_score""")
        result = cursor.fetchone()
        if result["max_tick"] is None:
            # no scores return 0's
            cursor.execute("SELECT id from teams where validated = 1")
            team_scores = dict()
            for result in cursor.fetchall():
                default = {"service_points": 0.0, "attack_points": 0.0, "sla": 1.0,
                           "total_points": 0.0, "num_valid_ticks": 0}
                team_scores[result["id"]] = default
            return team_scores
        tick_id = result["max_tick"]

    query = """SELECT service_points, attack_points, sla, total_points, num_valid_ticks, team_id
               FROM team_score
               WHERE tick_id = %s"""
    if base_team_id is not None:
        query += " AND total_points > " \
                 "(SELECT total_points from team_score WHERE team_id = %d and tick_id = %d)" % (base_team_id, tick_id)
    elif top_n is not None:
        query += " ORDER BY total_points DESC LIMIT %d" % top_n

    cursor.execute(query,
                   (tick_id,))

    team_scores = dict()
    for result in cursor.fetchall():
        team_scores[result["team_id"]] = result

    return team_scores



@app.route("/scores/store/tick/<int:tick_id>", methods=["POST"])
@requires_auth
def scores_store(tick_id):
    """The ``/scores/store/tick/<tick_id>`` endpoint requires authentication and,
    expects a dictionary of the updated scores as the post parameter ``scores``
    Note that this endpoint requires a POST request.

    It can be reached at
    ``/scores/store/tick/<tick_id>?secret=<API_SECRET>``.

    The JSON payload expected is
    {
    "scores": {
               team_id:
                       {
                        "service_points": service_points,
                        "attack_points": attack_points,
                        "sla": sla,
                        "total_points", total_points,
                        "num_valid_ticks": num_valid_ticks
                       }
              }
    }

    The JSON response is:

    {
      "result": "success" | "fail",
    }

    :param scores: the json payload
    :param int tick_id: the tick for which to store results
    :return: a JSON dictionary containing the result and upload_id
    """

    cursor = mysql.cursor()
    new_scores = json.loads(request.form.get("scores"))
    for team_id, scores_dict in new_scores.items():
        cursor.execute("""INSERT INTO team_score
                             (tick_id, team_id, sla,
                              attack_points, total_points, num_valid_ticks,
                              service_points)
                          VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                       (tick_id, team_id,
                        scores_dict["sla"],
                        scores_dict["attack_points"],
                        scores_dict["total_points"],
                        scores_dict["num_valid_ticks"],
                        scores_dict["service_points"]))

    # after inserting all of them commit
    # this makes sure they all got updated
    mysql.database.commit()

    return json.dumps({"result": "success"})


@app.route("/scores/firstbloods")
@app.route("/scores/firstbloods/tick/<int:tick_id>")
@requires_auth
def firstbloods(tick_id=None):
    """The ``/scores/firstbloods`` endpoint requires authentication and takes an
    optional ``tick_id`` argument. It returns all of the firstbloods that have occurred
    during tick_id if tick_id is present

    It can be reached at ``/scores/firstbloods?secret=<API_SECRET>``.

    It can also be reached at
    ``/scores/firstbloods/tick/<tick_id>?secret=<API_SECRET>``.

    The JSON response looks like::

    {
    "first_bloods": {
                      "service_id": {
                                     "team_id": team_id
                                     "service_id": service_id
                                     "service_name": service_name
                                     "time": time
                                    }
                    }
    }

    :param int tick_id: optional tick_id
    :return: a JSON dictionary of the first bloods
    """

    cursor = mysql.cursor()

    base_query = """SELECT fs.team_id, service_id, fs.created_on, tick_id,
                           services.name
                    FROM flag_submissions AS fs
                    JOIN services ON fs.service_id = services.id
                    WHERE result = 'correct'
                    GROUP BY service_id
                    HAVING fs.created_on = min(fs.created_on)"""

    if tick_id:
        cursor.execute(base_query + " AND fs.tick_id = %s", (tick_id,))
    else:
        cursor.execute(base_query)

    results = {}
    for result in cursor.fetchall():
        result["created_on"] = str(result["created_on"])
        service_id = result["service_id"]
        del result["service_id"]

        results[service_id] = result

    return json.dumps({"first_bloods": results})


# New and Simplified Scoring
@app.route("/flags/affected/tick/<int:tick_id>")
@requires_auth
def get_affected_flags_info(tick_id):
    """The ``/flags/affected/tick/`` endpoints requires
    authentication and expect no additional arguments.
    It fetches all the flags captured and lost by all the teams
    in the given tick.

    It can be reached at
    ``/flags/affected/tick/<tick_id>?secret=<API_SECRET>``

    The JSON response is::

        {
          "captured_flags" : {team_id:
                              {service_id:[
                                            {against_team_id: flag_id},
                                            ...
                                          ]
                              }
                    }
          "lost_flags" : {team_id:
                              {service_id:[
                                            {against_team_id: flag_id},
                                            ...
                                          ]
                              }
                    }
        }

    :param int tick_id: The target tick id for which the flags
           information is needed.
    :return: a JSON dictionary for each team with flag information.
    """
    # Initialize with all available teams
    teams_captured_flags = {}
    teams_lost_flags = {}
    all_teams = json.loads(teams_info())
    for team_id in all_teams["teams"]:
        # why is this returning a string?
        team_id = int(team_id)
        teams_captured_flags[team_id] = {}
        teams_lost_flags[team_id] = {}

    # Perform the main query
    cursor = mysql.cursor()
    cursor.execute("""SELECT fs.team_id as attacker_team_id, fl.team_id as owner_team_id, fs.service_id as service_id,
                             fs.flag_id as flag_id
                      FROM flag_submissions as fs, flags as fl
                      WHERE fs.tick_id = %s
                        AND fs.result = 'correct'
                        AND fs.flag_id = fl.id""", (tick_id,))

    for result in cursor.fetchall():
        attacker_team_id = result["attacker_team_id"]
        owner_team_id = result["owner_team_id"]
        service_id = result["service_id"]
        flag_id = result["flag_id"]
        if service_id not in teams_captured_flags[attacker_team_id]:
            teams_captured_flags[attacker_team_id][service_id] = []
        teams_captured_flags[attacker_team_id][service_id].append({owner_team_id: flag_id})

        # update lost flags, here we need to key against_team_id as it lost the flags
        if service_id not in teams_lost_flags[owner_team_id]:
            teams_lost_flags[owner_team_id][service_id] = []
        teams_lost_flags[owner_team_id][service_id].append({attacker_team_id: flag_id})

    response = {"captured_flags": teams_captured_flags, "lost_flags": teams_lost_flags}
    return json.dumps(response)


@app.route("/flags/wasexploited")
@app.route("/flags/wasexploited/tick/<int:tick_id>")
@requires_auth
def get_wasexploited(tick_id=None):
    """The ``/flags/wasexploited/tick/`` endpoints requires
    authentication and expect no additional arguments.
    It fetches all the flags captured and lost by all the teams
    in the given tick.

    It can be reached at
    ``/flags/wasexploited/tick/<tick_id>?secret=<API_SECRET>``
    ``/flags/wasexploited?secret=<API_SECRET>``

    The JSON response is::

        {
        team_id: {
                  service_id: {
                               "service_name": string,
                               "service_state": ("exploited",
                                                 "notexploited")
                              }
                 }
        }

    :param int tick_id: The target tick id for which the flags
           information is needed.
    :return: a JSON dictionary for each team with flag information.
    """

    cursor = mysql.cursor()
    if tick_id is None:
        tick_id, _, _, _ = get_current_tick(cursor)

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
            teams[team_id][service_id] = {"service_name": name, "service_state": "notexploited"}

    # Perform the main query
    cursor = mysql.cursor()
    cursor.execute("""SELECT DISTINCT fl.team_id as against_team_id, fs.service_id as service_id
                      FROM flag_submissions as fs, flags as fl
                      WHERE fs.tick_id = %s
                        AND fs.result = 'correct'
                        AND fs.flag_id = fl.id""", (tick_id,))

    for result in cursor.fetchall():
        against_team_id = result["against_team_id"]
        service_id = result["service_id"]
        teams[against_team_id][service_id]["service_state"] = "exploited"

    return json.dumps(teams)

@app.route("/flags/statistics")
@app.route("/flags/statistics/service/<int:service_id>")
@app.route("/flags/statistics/service/<int:service_id>/team/<int:team_id>")
@app.route("/flags/statistics/service/<int:service_id>/team/<int:team_id>/tick/<int:tick_id>")
@app.route("/flags/statistics/service/<int:service_id>/tick/<int:tick_id>")
@app.route("/flags/statistics/team/<int:team_id>")
@app.route("/flags/statistics/team/<int:team_id>/tick/<int:tick_id>")
@app.route("/flags/statistics/tick/<int:tick_id>")
@requires_auth
def flags_statistics(tick_id=None, team_id=None, service_id=None):
    """The ``/flags/statistics`` endpoints requires
    authentication and expect no additional arguments.
    It fetches all the flags captured and lost by all the teams
    in the given tick.

    It can be filtered by service_id, tick_id, or team_id (in any combination).

    It can be reached at
    ``/flags/statistics?secret=<API_SECRET>``

    The JSON response is::

          { team_id:
            { service_id:
              { "submitted": int
                "valid": int
              }
            }
          }

    :param int service_id: The service id for which the flags statistics are needed.
    :param int team_id: The team id for which the flags statistics are needed.
    :param int tick_id: The tick id for which the flags statistics are needed.
    :return: a JSON dictionary for each team with flag information.
    """
    cursor = mysql.cursor()

    where_tick_id, where_tick_id_value = "", []
    if tick_id is not None:
        where_tick_id = "WHERE tick_id = %s"
        where_tick_id_value = [tick_id]

    having = dict()
    if team_id is not None:
        having["team_id = %s"] = team_id

    if service_id is not None:
        having["service_id = %s"] = service_id

    having_stmt, having_stmts, having_values = "", [], []
    for stmt, value in having.items():
        if value is not None:
            having_stmts.append(stmt)
            having_values.append(value)
    if having_stmts:
        having_stmt = "HAVING " + " AND ".join(having_stmts)

    # Perform the main query
    cursor = mysql.cursor()
    cursor.execute("""SELECT team_id, service_id,
                             sum(case when result = 'correct' then 1 else 0 end) as valid,
                             count(*) as submitted
                        FROM flag_submissions
                          {}
                    GROUP BY team_id, service_id
                          {}""".format(where_tick_id, having_stmt),
                   where_tick_id_value + having_values)

    response = collections.defaultdict(lambda: collections.defaultdict(dict))
    for row in cursor.fetchall():
        team_id = row["team_id"]
        service_id = row["service_id"]
        response[str(team_id)][str(service_id)] = {"valid": str(row["valid"]),
                                                   "submitted": str(row["submitted"])}

    return json.dumps(response)


@app.route("/update/scores/tick/<int:tick_id>", methods=["POST"])
@requires_auth
def update_team_scores(tick_id):
    """The ``/update/scores/tick`` endpoint requires authentication and
    expects the ``tick_id`` as additional arguments. It is used to store the
    scores for team team for the given tick.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/update/scores/tick/<int:tick_id>?secret=<API_SECRET>``.

    It requires the following POST inputs:

    - sla_points, json dictionary containing sla points of each team:
        {
            team_id:<sla_points>,
            ...
        }
    - attack_points, json dictionary containing attack points of each team:
        {
            team_id:<attack_points>,
            ...
        }
    - defense_points, json dictionary containing defense points of each team:
        {
            team_id:<defense_points>,
            ...
        }
    - total_points, json dictionary containing total points of each team:
        {
            team_id:<total_points>,
            ...
        }

    The JSON response is::

        {
          "id": int
          "result": ("success", "failure")
        }

    :param int tick_id: the ID of the team that the scripts need to be ran against.
    :return: a JSON dictionary with a result status and an identifier of the
             run (for debugging purposes), to verify if updating the scores was
             successful.
    """

    team_sla_points = request.form.get("sla_points")
    team_attack_points = request.form.get("attack_points")
    team_defense_points = request.form.get("defense_points")
    team_total_points = request.form.get("total_points")
    all_teams = teams_info()
    cursor = mysql.cursor()
    # Iterate for each team.
    for curr_team_id in all_teams:
        sla_points = team_sla_points[curr_team_id]
        attack_points = team_attack_points[curr_team_id]
        defense_points = team_defense_points[curr_team_id]
        total_points = team_total_points[curr_team_id]
        cursor.execute("""INSERT INTO tick_scores
                                     (tick_id, team_id, sla_points,
                                      attack_points, defense_points, total_points)
                          VALUES (%s, %s, %s, %s, %s, %s)""", (tick_id, curr_team_id, sla_points,
                                                               attack_points, defense_points, total_points,))

    mysql.database.commit()

    run_id = cursor.lastrowid

    return json.dumps({"id": run_id,
                       "result": "success"})




