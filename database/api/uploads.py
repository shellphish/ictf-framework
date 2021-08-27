#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import request, abort

from . import app, mysql
from .utils import requires_auth


#@app.route("/uploads_ping")
@app.route("/uploads/ping")
def uploads_ping():
    return "sdaolpu"


# Uploading
#
@app.route("/upload/new", methods=["POST"])
@requires_auth
def upload_new():
    """The ``/upload/new`` endpoint requires authentication and,
    expects as arguments the ``team_id``, ``payload``, ``upload_type``, ``is_bundle``,
    ``upload_type`` is one of {"service", "exploit"}.
    If the ``upload_type`` is "exploit" then ``service_id`` is also required.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/upload/new?secret=<API_SECRET>``.

    The JSON response is:

        {
          "result": "success" | "fail",
          "upload_id": int
        }

    :param int team_id: the id of the team
    :param string name: name of the upload
    :param string payload: base64 encoded payload
    :param string upload_type: {"service", "exploit"}
    :param int is_bundle: whether or not it's bundled (0 or 1)
    :param int service_id: needed if the upload is an exploit
    :return: a JSON dictionary containing the result and upload_id
    """

    name = request.form.get("name")
    team_id = request.form.get("team_id")
    payload = request.form.get("payload")
    upload_type = request.form.get("upload_type")
    is_bundle = request.form.get("is_bundle")
    service_id = request.form.get("service_id", None)

    # check for invalid params
    if upload_type == "exploit" and service_id is None:
        return json.dumps({"result": "fail", "upload_id": None})

    if upload_type == "service" and service_id is not None:
        return json.dumps({"result": "fail", "upload_id": None})

    cursor = mysql.cursor()
    # if upload already exists for team do not add another, return success with a msg
    sql = """SELECT id
              FROM uploads
              WHERE team_id = %s
              AND name = %s
              AND upload_type = %s
              """
    print(sql % (team_id, name, upload_type))
    cursor.execute(sql, (team_id, name, upload_type))

    result = cursor.fetchone()

    if cursor.rowcount > 0:
        upload_id = result["id"]

        cursor.execute("""UPDATE uploads 
                          SET payload=%s, upload_type = %s, is_bundle=%s 
                          WHERE id = %s  
                          """,
                       (payload, upload_type, is_bundle, upload_id))

        mysql.database.commit()

        return json.dumps({"result": "update succeeded",
                           "id": upload_id})


    cursor.execute("""INSERT INTO uploads
                          (team_id, name, payload, upload_type, is_bundle, service_id)
                      VALUES (%s, %s, %s, %s, %s, %s)""",
                   (team_id, name, payload, upload_type, is_bundle, service_id))

    mysql.database.commit()
    if cursor.rowcount == 0:
        return json.dumps({"result": "fail", "upload_id": None})
    else:
        upload_id = cursor.lastrowid
        return json.dumps({"result": "success", "upload_id": upload_id})


@app.route("/uploads")
@requires_auth
def uploads():
    """The ``/uploads`` endpoint requires authentication

    It can be reached at
    ``/uploads?secret=<API_SECRET>``

    The JSON response is:
        {"uploads": [{
                        "id": int,
                        "team_id": int,
                        "name": string,
                        "upload_type": one of {"service", "exploit"}
                        "is_bundle": 0 or 1
                        "service_id": int for scripts, null for services
                        "feedback": string
                        "state": one of "untested", "working", "notworking"
                        "created_on": timestamp
                    }]

    :return: a JSON dictionary containing the upload data
    """

    cursor = mysql.cursor()

    # we don't return payloads from this endpoint
    cursor.execute("""SELECT id, team_id, name, upload_type, is_bundle,
                             service_id, feedback, state, created_on
                      FROM uploads""")
    uploads = cursor.fetchall()

    # created_on, payload must be a string
    for upload_row in uploads:
        upload_row["created_on"] = str(upload_row["created_on"])

    return json.dumps({"uploads": uploads})


@app.route("/upload/get/<int:upload_id>")
@requires_auth
def upload_get(upload_id=None):
    """The ``/upload/get/`` endpoint requires authentication and
    takes an ``upload_id`` parameter

    It can be reached at
    ``/upload/get/<int:upload_id>?secret=<API_SECRET>``

    The JSON response is:
        {
            "id": int,
            "team_id": int,
            "name": string,
            "payload": base64 string,
            "upload_type": one of {"service", "exploit"}
            "is_bundle": 0 or 1
            "service_id": int for scripts, null for services
            "feedback": string
            "state": one of "untested", "working", "notworking"
            "created_on": timestamp
        }

    :param int upload_id: the id of the team
    :return: a JSON dictionary containing the upload data
    """

    cursor = mysql.cursor()

    cursor.execute("""SELECT id, team_id, name, payload, upload_type, is_bundle,
                             service_id, feedback, state, created_on
                      FROM uploads
                      WHERE id = %s""", (upload_id,))
    upload_row = cursor.fetchone()

    if upload_row is None:
        abort(400)

    # created_on, payload must be a string
    upload_row["created_on"] = str(upload_row["created_on"])
    upload_row["payload"] = str(upload_row["payload"])

    return json.dumps(upload_row)


@app.route("/upload/untested/type/<string:upload_type>")
@requires_auth
def upload_untested_type(upload_type):
    """The ``/upload/untested/type/`` endpoint requires authentication and
    takes an ``upload_type`` parameter

    It can be reached at
    ``/upload/untested/type/<string:upload_type>?secret=<API_SECRET>``

    The JSON response is a list of untested uploads, sorted by when they were created,
    which looks like:
        {"uploads":
            [{"id": int,
              "team_id": int,
              "name": string,
              "payload": base64 string,
              "upload_type": one of {"service", "exploit"}
              "is_bundle": 0 or 1
              "service_id": int for scripts, null for services
              "feedback": string
              "state": one of "untested", "working", "notworking"
              "created_on": timestamp
            }]

    :param string upload_type: the type of uploads to retrieve
    :return: a JSON list of dictionaries containing the upload data
    """

    cursor = mysql.cursor()

    cursor.execute("""SELECT id, team_id, name, payload, upload_type, is_bundle,
                             service_id, feedback, state, created_on
                      FROM uploads
                      WHERE upload_type = %s AND state = 'untested'
                      ORDER BY created_on ASC""",
                   (upload_type,))
    untested_uploads = cursor.fetchall()

    # created_on, payload must be a string
    for upload in untested_uploads:
        upload["created_on"] = str(upload["created_on"])
        upload["payload"] = str(upload["payload"])

    return json.dumps({"uploads": untested_uploads})


@app.route("/upload/status")
@app.route("/upload/status/team/<int:team_id>")
@requires_auth
def upload_status(team_id=None):
    """The ``/upload/status/`` endpoint requires authentication and
    takes an optional ``team_id`` parameter

    It can be reached at
    ``/upload/status``
    ``/upload/status/team/<team_id>?secret=<API_SECRET>``.

    The JSON response is like:
        {"uploads":
            [{"id": int,
              "team_id": int,
              "name": string,
              "payload": base64 string,
              "upload_type": one of {"service", "exploit"}
              "is_bundle": 0 or 1
              "service_id": int for scripts, null for services
              "feedback": string
              "state": one of "untested", "working", "notworking"
              "created_on": timestamp
            }]

    :param int team_id: the id of the team
    :return: a JSON dictionary containing the status of the uploads
    """

    base_query = """SELECT id, team_id, payload, upload_type, service_id,
                           feedback, state, created_on
                      FROM uploads"""

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

    cursor = mysql.cursor()

    if filter_stmt:
        cursor.execute("{} WHERE {}".format(base_query, filter_stmt),
                       filter_values)
    else:
        cursor.execute(base_query)

    uploads_data = cursor.fetchall()

    # created_on must be a string
    for upload in uploads_data:
        upload["created_on"] = str(upload["created_on"])
        upload["payload"] = str(upload["payload"])

    return json.dumps({"uploads": uploads_data})


@app.route("/upload/update/<int:upload_id>", methods=["POST"])
@requires_auth
def upload_update(upload_id):
    """The ``/upload/update/<upload_id>`` endpoint requires authentication and
    expects an ``upload_id`` argument.
    If any of the following arguments are provided they will be updated:
    ``payload``, ``feedback``, ``state``. ``service_id``, ``is_bundle``
    ``state`` should be one of {'untested', 'working', 'notworking'}

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/service/uploads/update?secret=<API_SECRET>``.

    The JSON response is:

        {
          "result": "success" | "fail",
          "upload_id": int
        }

    :param int upload_id: the id of the upload
    :param string payload: base64 encoded payload
    :param int is_bundle: (1|0, 1 if a bundle, 0 if not),
    :param string feedback: feedback message
    :param string state: one of {'untested', 'working', 'notworking'}
    :param int service_id: optional service id
    :return: a JSON dictionary containing the result and upload_id
    """

    payload = request.form.get("payload", None)
    feedback = request.form.get("feedback", None)
    team_id = request.form.get("team_id", None)
    state = request.form.get("state", None)
    service_id = request.form.get("service_id", None)
    is_bundle = request.form.get("is_bundle", None)

    # dynamically create the update statement
    updates = dict()
    updates["payload = %s"] = payload
    updates["feedback = %s"] = feedback
    updates["team_id = %s"] = team_id
    updates["state = %s"] = state
    updates["service_id = %s"] = service_id
    updates["is_bundle = %s"] = is_bundle

    # We cannot use a dict comprehension here with keys() and values() after
    # because their order is not guaranteed to be the same.
    update_stmts, update_values = [], []
    for stmt, value in updates.items():
        if value is not None:
            update_stmts.append(stmt)
            update_values.append(value)
    update_stmt = ", ".join(update_stmts)

    cursor = mysql.cursor()
    cursor.execute("UPDATE uploads SET {} WHERE id = %s".format(update_stmt),
                   tuple(update_values + [upload_id]))

    mysql.database.commit()
    upload_id = cursor.lastrowid
    return json.dumps({"result": "success", "upload_id": upload_id})
