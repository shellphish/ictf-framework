# Scores old stuff
#
# Helper functions
#
# FIXME: use ticks instead, teams are either up for the whole tick or down for the whole tick
def _get_uptime_for_team(team_id, cursor):
    """Calculate the uptime for a team.

    The uptime is normalized to 0 to 100. An uptime of 100 means the team was
    online for the entire tick, while an uptime of 0 means it was not online
    at all.

    :param int team_id: ID of the team.
    :param cursor: Cursor that points to the MySQL database.

    :return: Uptime of the team, between [0, 100]
    """
    # FIXME: This currently does not work for disabled and enabled services.
    #        We should calculate the uptime per tick.
    # Fetch total number of total tests made
    cursor.execute("""SELECT COUNT(id) AS count, service_id
                      FROM team_service_state WHERE team_id = %s
                                              GROUP BY service_id""",
                   (team_id,))
    total_counts = dict()
    for result in cursor.fetchall():
        total_counts[result["service_id"]] = result["count"]

    # Fetch number of tests that were successful (up and working)
    cursor.execute("""SELECT COUNT(id) AS count, service_id
                      FROM team_service_state WHERE team_id = %s
                                                AND state = 'up'
                                              GROUP BY service_id""",
                   (team_id,))
    up_counts = {}
    for result in cursor.fetchall():
        up_counts[result["service_id"]] = result["count"]

    # Calculate the average uptime
    services = len(total_counts.keys())
    avg_uptime = 0
    for service_id, total in total_counts.items():
        up_ = up_counts[service_id]
        uptime = (up_ * 1.) / (total * 1.)
        avg_uptime += uptime / services

    return avg_uptime * 100


@app.route("/scores_deprecated")
@requires_auth
def scores_deprecated():
    """The ``/scores`` endpoint requires authentication and expects no
    additional argument. It is used to retrieve the current scores for each
    team.

    It can be reached at ``/scores?secret=<API_SECRET>``.

    The JSON response is::

        {
          "scores": {team_id: {score: int,
                               sla: int (0-100, percentage),
                               raw_score: int }}
        }

    :return: a JSON dictionary containing status information on the flag.
    """
    cursor = mysql.cursor()

    cursor.execute("""SELECT team_id, name as team_name, SUM(score) AS score
                      FROM team_score
                      JOIN teams ON teams.id = team_score.team_id
                      GROUP BY team_id""")

    scores_ = {}
    # Currently, we are multiplying overall score with overall SLA. Do we
    # actually want to do this, or do we want do calculate this per tick?
    for result in cursor.fetchall():
        team_id = result["team_id"]
        team_name = result["team_name"]
        raw_score = int(result["score"])
        sla_percentage = _get_uptime_for_team(team_id, cursor)
        scores_[team_id] = {"team_name": team_name,
                            "raw_score": raw_score,
                            "sla": int(sla_percentage),
                            "score": raw_score * (sla_percentage / 100.)}

    return json.dumps({"scores": scores_})
