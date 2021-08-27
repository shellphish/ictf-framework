#!/usr/bin/env python
# -*- coding: utf-8 -*-

import base64
import collections
import hashlib
import hmac
import json
import random
import sys
import string

from flask import request

from . import app, mysql, db_helpers
from .utils import requires_auth, get_current_tick


#@app.route("/teams_ping")
@app.route("/teams/ping")
@app.route("/team/ping")
def teams_ping():
    return "smaet"

# Python 3 compatibility
#
PY3 = sys.version_info[0] == 3

# pylint:disable=invalid-name
if PY3:
    string_types = str,         # pragma: no flakes
    text_type = str             # pragma: no flakes
else:
    string_types = basestring,  # pragma: no flakes
    text_type = unicode         # pragma: no flakes
# pylint:enable=invalid-name


# Helper functions
#
def _generate_new_flag():
    """Generate a new flag, based on our game settings.

    :return: Flag following the predefined flag format.
    """
    flag = "".join(random.choice(app.config["FLAG_ALPHABET"])
                   for _ in range(app.config["FLAG_LENGTH"]))
    return "{0[FLAG_PREFIX]}{1}{0[FLAG_SUFFIX]}".format(app.config, flag)


def encode_string(string):
    """Encodes a string to bytes, if it isn't already.

    :param str string: the string to encode.
    """

    if isinstance(string, text_type):
        string = string.encode('utf-8')
    return string


def hash_password(password):
    salt = app.config["USER_PASSWORD_SALT"]
    hmac_ = hmac.new(encode_string(salt), encode_string(password),
                     hashlib.sha512)
    password_hashed = base64.b64encode(hmac_.digest())
    return password_hashed

# Team login with token only
#

@app.route("/team/token/login", methods=["POST"])
@requires_auth
def team_toke_login():
    """The ``/team/authenticate`` endpoint requires authentication and expects
    no additional argument. It is used to authenticate a team and the team_id
    and status

    Note that this endpoint is an exception. It requires a POST request
    although it does *not* modify the state on the database.

    It can be reached at ``/team/token/login?secret=<API_SECRET>``.

    The JSON response is::

        {
            "result": "success",
            "id": int,
            "validated": 1 or 0
        }

    or::

        {
            "result": "failure"
        }

    :param str login_token: the plaintext password.
    :return: a JSON dictionary with with status code "success" and the team id,
             or just a JSON dictionary with the status code "failure".
    """
    login_token = request.form.get("login_token", None)
    cursor = mysql.cursor()

    if login_token is not None:
        cursor.execute("""SELECT id, validated FROM teams
                          WHERE login_token = %s """,
                       (login_token,))
    else:
        flag_token = request.form.get("flag_token", None)
        cursor.execute("""SELECT id, validated FROM teams
                                  WHERE flag_token = %s or login_token = %s""",
                       (flag_token, flag_token, ))


    row = cursor.fetchone()

    if row:
        team_id = row["id"]
        validated = row["validated"]
        return json.dumps({"result": "success",
                           "validated": validated,
                           "id": team_id})

    return json.dumps({"result": "failure incorrect login"})


# Team login
#
@app.route("/team/authenticate", methods=["POST"])
@requires_auth
def team_authenticate():
    """The ``/team/authenticate`` endpoint requires authentication and expects
    no additional argument. It is used to authenticate a team and the team_id
    and status

    Note that this endpoint is an exception. It requires a POST request
    although it does *not* modify the state on the database.

    It can be reached at ``/team/authenticate?secret=<API_SECRET>``.

    The JSON response is::

        {
            "result": "success",
            "id": int,
            "validated": 1 or 0
        }

    or::

        {
            "result": "failure"
        }

    :param str email: the email address that wants to authenticate.
    :param str password: the plaintext password.
    :return: a JSON dictionary with with status code "success" and the team id,
             or just a JSON dictionary with the status code "failure".
    """
    email = request.form.get("email")
    password = request.form.get("password")
    cursor = mysql.cursor()

    password_encrypted = hash_password(password)

    cursor.execute("""SELECT id, validated FROM teams
                      WHERE email = %s AND password = %s""",
                   (email, password_encrypted))
    row = cursor.fetchone()

    if row:
        team_id = row["id"]
        validated = row["validated"]
        return json.dumps({"result": "success",
                           "validated": validated,
                           "id": team_id})

    return json.dumps({"result": "failure"})


@app.route("/team/academic/<int:team_id>")
@requires_auth
def is_academic_team(team_id):
    """The ``/team/academic/<int:team_id>`` endpoint requires authentication and expects
    a team id. It is used to determine a teams academic status.

    It can be reached at ``/team/academic/<int:team_id>?secret=<API_SECRET>``.

    The JSON response is::

        {
            "result": "success",
            "id": int,
            "academic_team": 1 or 0
            "is_academic": True or False
        }

    or::

        {
            "result": "failure"
        }

    :param int team_id: the id of the team being checked.
    :return: a JSON dictionary with with status code "success" and the team id,
             or just a JSON dictionary with the status code "failure".
    """
    cursor = mysql.cursor()

    cursor.execute("""SELECT id, academic_team FROM teams
                      WHERE id = %s """,
                   (team_id,))
    row = cursor.fetchone()

    if row:
        team_id = row["id"]
        academic_team = row["academic_team"]
        return json.dumps({"result": "success",
                           "academic_team": academic_team,
                           "is_academic" : (academic_team != 0),
                           "id": team_id})

    return json.dumps({"result": "failure"})





@app.route("/team/changepass", methods=["POST"])
@requires_auth
def team_changepass():
    """The ``/team/changepass`` endpoint requires authentication and expects
    the ``team_id`` and ``password`` as arguments. The team's password
    will be set to ``password``

    Note that this endpoint requires a POST request.

    It can be reached at ``/team/changepass?secret=<API_SECRET>``.

    The JSON response is::

        {
            "result": "success" or "fail"
        }

    :param int team_id: the team_id whose password to change.
    :param str password: the new plaintext password.
    :return: a JSON dictionary with with status code "success" or "fail"
    """
    team_id = request.form.get("team_id")
    password = request.form.get("password")
    cursor = mysql.cursor()

    password_encrypted = hash_password(password)

    cursor.execute("""UPDATE teams SET password = %s
                      WHERE id = %s""",
                   (password_encrypted, team_id))

    mysql.database.commit()

    if cursor.rowcount == 0:
        return json.dumps({"result": "fail"})
    else:
        return json.dumps({"result": "success"})


# Team
#
@app.route("/team/add", methods=["POST"])
@requires_auth
def team_add():
    """The ``/team/add`` endpoint requires authentication and expects the
    following arguments: ``name``, ``country``, ``logo``, ``team_email``
                         ``team_password``. ``url``


    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/add?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail"
          "team_id": int
          "fail_reason": null | "team email already in use"
                              | "team name already in use"
                              | "unknown"
    }

    :param string name: the name of the team.
    :param string country: the two character country code
    :param string url: team url
    :param string logo: base64 encoded image
    :param string team_email: team login email
    :param string team_password: team login password
    :param string academic_team: is 1 if it is an academic team and 0 otherwise
    :return: a JSON dictionary containing the result, team_id, and an optional fail_reason
    """

    name = request.form.get("name")
    country = request.form.get("country", None)
    logo = request.form.get("logo", None)
    url = request.form.get("url", None)
    team_email = request.form.get("team_email")
    team_password = request.form.get("team_password")
    hashed_password = hash_password(team_password)
    academic_team = request.form.get("academic_team", 0)
    login_token = request.form.get("login_token", None)
    flag_token = request.form.get("flag_token", None)
    if login_token is None or flag_token is None:
        return json.dumps({"result": "failed", "team_id": "NA", "fail_reason": "A flag or login token was missing"})

    cursor = mysql.cursor()
    result, team_id, fail_reason = create_team(cursor, name, country, logo, url, team_email, team_password,
                                               hashed_password, academic_team, login_token, flag_token)
    return json.dumps({"result": result, "team_id": team_id, "fail_reason": fail_reason})



# Team
#
@app.route("/team/get_team_id", methods=["POST"])
@requires_auth
def team_get_id_by_flagtoken():

    flag_token = request.form.get("token")

    if login_token is None or flag_token is None:
        return json.dumps({"result": "failed", "team_id": "NA", "fail_reason": "A flag or login token was missing"})

    cursor = mysql.cursor()
    result, team_id, fail_reason = create_team(cursor, name, country, logo, url, team_email, team_password,
                                               hashed_password, academic_team, login_token, flag_token)
    return json.dumps({"result": result, "team_id": team_id, "fail_reason": fail_reason})


@app.route("/team/add_direct", methods=["POST"])
@requires_auth
def team_add_direct():
    """The ``/team/add_direct`` endpoint requires authentication and expects the
    following arguments: ``id``, ``name``, ``country``, ``logo``, ``team_email``
                         ``team_password``. ``url``

    We need to use a direct add when we already know the ID we want for the team.
    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/add_direct?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail"
          "team_id": int
          "fail_reason": null | "team email already in use"
                              | "team name already in use"
                              | "team id already in use"
                              | "unknown"
    }

    :param string name: the name of the team.
    :param string country: the two character country code
    :param string url: team url
    :param string logo: base64 encoded image
    :param string team_email: team login email
    :param string team_password: team login password
    :param string academic_team: is 1 if it is an academic team and 0 otherwise
    :param string login_token: is the token used by the team to login
    :param string academic_team: is the token used by the team to submit flags
    :return: a JSON dictionary containing the result, team_id, and an optional fail_reason
    """

    name = request.form.get("name")
    team_id = request.form.get("id")    
    country = request.form.get("country", None)
    logo = request.form.get("logo", None)
    url = request.form.get("url", None)
    team_email = request.form.get("team_email")
    team_password = request.form.get("team_password")
    hashed_password = hash_password(team_password)
    academic_team = request.form.get("academic_team", 0)
    login_token = request.form.get("login_token", None)
    flag_token = request.form.get("flag_token", None)

    if login_token is None or flag_token is None:
        return json.dumps({"result": "failed", "team_id": team_id, "fail_reason": "A flag or login token was missing"})

    cursor = mysql.cursor()

    result, team_id, fail_reason = create_team(cursor, name, country, logo, url, team_email, team_password,
                                               hashed_password, academic_team, team_id, login_token, flag_token)
    return json.dumps({"result": result, "team_id": team_id, "fail_reason": fail_reason})

def create_team(cursor, name, country, logo, url, team_email, team_password, hashed_password, academic_team,
                team_id = None, login_token=None, flag_token=None):
    """
    This method will actually create the team. 

    :return: a tuple (string result, int team_id, string fail_reason), described `team_add` and `team_add_direct`
    """
    def check_for_existing(column_name, value):
        """
        Small helper function, check if a column with the value exists in the team table, 
        :return: True if it exists, False if it does not
        """
        query = """SELECT COUNT(*) as count FROM teams WHERE """ + column_name + """ = %s"""
        cursor.execute(query, (value,))
        result = cursor.fetchone()
        return result["count"] != 0

    # Sanity checks
    if team_id != None:
        if check_for_existing('id', team_id):
            return ("fail", None, "team id already in use")
    
    if check_for_existing('email', team_email):
        return ("fail",  None, "team email already in use")

    if check_for_existing('name', name):
        return ("fail", None, "team name already in use")

    if team_id == None:
        cursor.execute("""INSERT INTO teams
                                      (name, logo, url, country, email, password, academic_team, login_token, flag_token)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                       (name, logo, url, country, team_email, hashed_password, academic_team, login_token, flag_token))
    else:
        cursor.execute("""INSERT INTO teams
                                      (id, name, logo, url, country, email, password, academic_team, login_token, flag_token)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                       (team_id, name, logo, url, country, team_email, hashed_password, academic_team, login_token, flag_token))
        
    team_id = cursor.lastrowid

    mysql.database.commit()

    return ("success", team_id, None)


@app.route("/team/update/<int:team_id>", methods=["POST"])
@requires_auth
def team_update(team_id):
    """The ``/team/add`` endpoint requires authentication and expects the team_id as an argument

    If any of the following arguments are provided they will be updated:
    ``country``, ``logo``, ``url``, ``validated``

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/update?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail"
        }

    :param int team_id: the id of the team
    :param string country: the two character country code
    :param string url: team url
    :param string logo: base64 encoded image
    :param int validated: 1 or 0 representing whether or not the team has been validated

    :return: a JSON dictionary containing the result
    """

    name = request.form.get("name", None)
    country = request.form.get("country", None)
    logo = request.form.get("logo", None)
    url = request.form.get("url", None)
    validated = request.form.get("validated", None)
    email = request.form.get("email", None)
    academic_team = request.form.get("academic_team", None)

    # dynamically create the update statement
    updates = dict()
    if name is not None:
        print("trying to update name")
        updates["name = %s"] = name

    updates["country = %s"] = country
    updates["logo = %s"] = logo
    updates["email = %s"] = email

    if url is not None:
        updates["url = %s"] = url

    if validated is None:
        updates["validated = %s"] = "1"
    else:
        updates["validated = %s"] = validated


    if academic_team is None:
        updates["academic_team = %s"] = 1
    else:
        updates["academic_team = %s"] = academic_team

    # We cannot use a dict comprehension here with keys() and values() after
    # because their order is not guaranteed to be the same.
    update_stmts, update_values = [], []
    for stmt, value in updates.items():
        if value is not None:
            update_stmts.append(stmt)
            update_values.append(value)

    update_stmt = ", ".join(update_stmts)

    cursor = mysql.cursor()

    print("UPDATE teams SET {} WHERE id = %s".format(update_stmt), tuple(update_values + [team_id]))

    cursor.execute("UPDATE teams SET {} WHERE id = %s".format(update_stmt), tuple(update_values + [team_id]))
    mysql.database.commit()

    return json.dumps({"result": "success"})

@app.route("/team/key/get/<int:team_id>")
@requires_auth
def team_key_get(team_id):
    """The ``/game/on`` endpoint does not require auth
       It looks for an entry in game table, which means the game has started

       It can be reached at
       ``/game/on``.

       :return: JSON containing game_id.
       """
    to_return = {}

    try :
        cursor = mysql.cursor()

        cursor.execute("SELECT team_id, ctf_key, root_key, ip, port FROM team_vm_key WHERE team_id = %s ", (team_id,))

        key_cursor = cursor.fetchone()
        if key_cursor is None:
            to_return["num"] = "404"
            to_return["msg"] = "team not found"
            return json.dumps(to_return)
        to_return["team_id"] = key_cursor["team_id"]
        to_return["ctf_key"] = key_cursor["ctf_key"]
        #to_return["root_key"] = key_cursor["root_key"]
        to_return["ip"] = key_cursor["ip"]
        #to_return["port"] = key_cursor["port"]
        return json.dumps(to_return)

    except Exception as e:
        print(e)
        return json.dumps({"result": "failure", "reason": str(e)})


@app.route("/team/vm/get/<int:team_id>")
@requires_auth
def team_vm_get(team_id):

    to_return = {}

    try :
        cursor = mysql.cursor()

        cursor.execute("SELECT team_id, ctf_key, root_key, ip, port FROM team_vm_key WHERE team_id = %s ", (team_id,))

        key_cursor = cursor.fetchone()
        if key_cursor is None:
            to_return["num"] = "404"
            to_return["msg"] = "team not found"
            return json.dumps(to_return)
        to_return["team_id"] = key_cursor["team_id"]
        to_return["ctf_key"] = key_cursor["ctf_key"]
        #to_return["root_key"] = key_cursor["root_key"]
        to_return["ip"] = key_cursor["ip"]
        #to_return["port"] = key_cursor["port"]
        return json.dumps(to_return)

    except Exception as e:
        print(e)
        return json.dumps({"result": "failure", "reason": str(e)})

@app.route("/team/update/keys/<int:team_id>", methods=["POST"])
@requires_auth
def team_update_keys(team_id):
    """The ``/team/add/keys`` endpoint requires authentication and expects the team_id as an argument

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/update/keys/<int:team_id>>?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail"
          "team_id": int
        }

    :param int team_id: the id of the team
    :param string ctf_key: the new ctf users private key
    :param string root_key:  the new root users private key
    :return: a JSON dictionary containing the result
    """
    try:
        ctf_key = request.form.get("ctf_key", None)
        root_key = request.form.get("root_key", None)
        ip = request.form.get("ip", None)
        port = request.form.get("port", None)

        cursor = mysql.cursor()
        cursor.execute("""UPDATE team_vm_key
                                  SET ctf_key = %s,
                                      root_key = %s,
                                      ip = %s,
                                      port = %s
                              WHERE team_id = %s""",
                       (ctf_key, root_key, ip, port, team_id))
        mysql.database.commit()

        return json.dumps({"result": "success", "team_id": team_id})
    except Exception as e:
        print(e)
        return json.dumps({"result": "failure", "reason": str(e)})

@app.route("/team/add/keys/<int:team_id>", methods=["POST"])
@requires_auth
def team_add_keys(team_id):
    """The ``/team/add/keys`` endpoint requires authentication and expects the team_id as an argument

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/add/keys/<int:team_id>>?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail"
          "team_id": int
        }

    :param int team_id: the id of the team
    :param string ctf_key: ctf users private key
    :param string root_key:  root users private key
    :return: a JSON dictionary containing the result
    """
    try:
        ctf_key = request.form.get("ctf_key", None)
        root_key = request.form.get("root_key", None) #useless
        ip = request.form.get("ip", None)
        port = request.form.get("port", None) #useless

        cursor = mysql.cursor()
        cursor.execute("""INSERT INTO team_vm_key
                                  (team_id, ctf_key, root_key, ip, port)
                              VALUES (%s, %s, %s, %s, %s )""",
                       (team_id, ctf_key, root_key, ip, port))
        result_team_id = cursor.lastrowid

        mysql.database.commit()

        return json.dumps({"result": "success", "team_id": result_team_id})
    except Exception as e:
        print(e)
        return json.dumps({"result": "failure", "reason": str(e)})

# Metadata
#
#@app.route("/metadata/labels/add", methods=["POST"])
@app.route("/teams/metadata/labels/add", methods=["POST"])
@requires_auth
def metadata_labels_add():
    """The ``/teams/metadata/labels/add`` endpoint requires authentication and expects the
    argument ``description``. It adds a label to the metadata associated with teams.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/teams/metadata/labels/add?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail"
          "id": int
        }

    :param string description: the description of the metadata.
    :return: a JSON dictionary containing the result and id of the label
    """

    description = request.form.get("description")
    label = request.form.get("label")
    cursor = mysql.cursor()

    cursor.execute("""INSERT INTO team_metadata_labels
                          (label, description)
                      VALUES (%s, %s)""",
                   (label, description))
    mysql.database.commit()

    return json.dumps({"result": "success"})


#@app.route("/metadata/labels")
@app.route("/teams/metadata/labels")
@requires_auth
def metadata_labels():
    """The ``/teams/metadata/labels`` endpoint requires authentication and takes no arguments.
    It returns the metadata labels currently defined.

    It can be reached at
    ``/teams/metadata/labels?secret=<API_SECRET>``.

    The JSON response is::

        {"result" : [{
                      "description": string
                      "id": int
                    }]
        }

    :return: a JSON dictionary containing the result and id of the label
    """

    cursor = mysql.cursor()
    cursor.execute("""SELECT id, description from team_metadata_labels""")
    labels = cursor.fetchall()

    return json.dumps({"result": labels})


@app.route("/team/metadata/add/<int:team_id>", methods=["POST"])
@requires_auth
def team_metadata_add(team_id):
    """The ``/team/metadata/add`` endpoint requires authentication and requires the team_id
    and ``label_data_json`` a json dictionary of the label_id to response

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/metadata/add/<team_id>?secret=<API_SECRET>``.

    The JSON response is:: {"result": "success"}

    :return: a JSON dictionary containing the result and id of the label
    """

    label_data_json = request.form.get("label_data_json")
    label_data = json.loads(label_data_json)

    # make into list for executemany command
    data = []
    for k, v in label_data.items():
        # the value appears twice for the update %s on duplicate key
        data.append((k, v, team_id, v))

    cursor = mysql.cursor()
    stmt = """INSERT INTO team_metadata (team_metadata_label_id, content, team_id)
                VALUES (%s, %s, %s)
              ON DUPLICATE KEY UPDATE content=%s"""

    for values in data:
        cursor.execute(stmt, values)

    mysql.database.commit()

    return json.dumps({"result": "success"})


#@app.route("/metadata")
#@app.route("/metadata/team/<int:team_id>")
#@app.route("/metadata/label/<int:label_id>")
#@app.route("/metadata/label/<int:label_id>/team/<int:team_id>")
@app.route("/teams/metadata")
@app.route("/teams/metadata/team/<int:team_id>")
@app.route("/teams/metadata/label/<int:label_id>")
@app.route("/teams/metadata/label/<int:label_id>/team/<int:team_id>")
@requires_auth
def metadata(label_id=None, team_id=None):
    """The ``/teams/metadata`` endpoint requires authentication and can take an
    optional ``team_id`` or ``label_id``. It returns all the metadata associated
    with the teams.

    Additional server-side filtering is possible, by:

    - team
    - label

    - ``/teams/metadata/team/<team_id>?secret=<API_SECRET>``.
    - ``/teams//metadata/label/<label_id>?secret=<API_SECRET>``.
    - ``/teams//metadata/label/<label_id>/team/<team_id>?secret=<API_SECRET>``.

    The JSON response looks like::

        {
          "metadata" : [List of {"id" : int,
                                "team_id": int,
                                "team_metadata_label_id": int,
                                "description", string
                                "content": string
        }

    :param int label_id: optional ID of the metadata label for which the metadata
                           should be fetched.
    :param int team_id: optional ID of the team whose metadata should be
                        fetched.
    :return: a JSON dictionary that contains all metadata that match the
             filter.
    """
    cursor = mysql.cursor()

    base_query = """SELECT team_metadata.id as id, description, team_metadata_label_id,
                           content
                    FROM team_metadata JOIN team_metadata_labels
                    ON team_metadata_labels.id = team_metadata.team_metadata_label_id"""

    # Dynamically create the WHERE statement
    filters = dict()
    filters["team_metadata_label_id = %s"] = label_id
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

    return json.dumps({"metadata": cursor.fetchall()})


@app.route("/team/info/id/<int:team_id>")
@app.route("/team/info/email/<string:email>")
@requires_auth
def team_info(team_id=None, email=None):
    """The ``/team/info`` endpoint requires authentication and
    expects either the ``team_id`` or the ``email`` as an additional argument.

    It can be reached at ``/team/info/id/<int:team_id>?secret=<API_SECRET>``.
    It can be reached at ``/team/info/email/<string:email>?secret=<API_SECRET>``.

    The JSON response is::

        {
            "id": int,
            "name": string,
            "url": string,
            "country": string,
            "email": string
        }

    :param int team_id: the id of the team to retrieve information on.
    :param string email: the email of the team to retrieve information on.
    :return: a JSON dictionary containing basic information on a team.
    """
    cursor = mysql.cursor()

    # Dynamically create the WHERE statement
    filters = dict()
    filters["email = %s"] = email
    filters["id = %s"] = team_id

    # We cannot use a dict comprehension here with keys() and values() after
    # because their order is not guaranteed to be the same.
    filter_stmts, filter_values = [], []
    for stmt, value in filters.items():
        if value is not None:
            filter_stmts.append(stmt)
            filter_values.append(value)
    filter_stmt = " AND ".join(filter_stmts)
    filter_values = tuple(filter_values)

    cursor.execute("""SELECT id, name, url, country,
                             logo, email, validated
                        FROM teams
                       WHERE {}"""
                   .format(filter_stmt), filter_values)

    team = cursor.fetchone()

    # this is probably inefficient
    cursor.execute("""SELECT latency, packetloss
                        FROM team_connectivity_log
                       WHERE team_id = %s
                         AND created_on = (SELECT max(created_on)
                                             FROM team_connectivity_log
                                            WHERE team_id = %s)""",
                    (team["id"], team["id"]))

    try:
        team.update(cursor.fetchone())
    except TypeError:
        pass
    if 'logo' in team:
        team['logo'] = team['logo'].decode('utf-8')
    return json.dumps(team)


@app.route("/team/latency/<int:team_id>", methods=["POST"])
@requires_auth
def team_latency(team_id):
    """The ``/team/latency`` endpoint requires authentication and expects the team_id as an argument

    If any of the following arguments are provided they will be updated:
    ``latency``, ``packetloss``

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/latency/<int:team_id>?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": "success" | "fail",
          "message": <an optional message in case of fail>
        }

    :param int team_id: the id of the team
    :param double latency: the latency to the team
    :param double packetloss: the packetloss of the team
    :return: a JSON dictionary containing the result
    """

    latency = request.form.get("latency", None)
    packetloss = request.form.get("packetloss", None)

    if latency is None or packetloss is None:
        return json.dumps({"result": "fail",
                           "message": "missing latency or packetloss"})

    cursor = mysql.cursor()
    cursor.execute("""INSERT INTO team_connectivity_log
                         (team_id, latency, packetloss)
                      VALUES (%s,%s,%s)""", (team_id, latency, packetloss))
    mysql.database.commit()

    return json.dumps({"result": "success"})


@app.route("/team/vote/services", methods=["POST"])
@requires_auth
def team_vote_services():
    """The ``/team/vote/services/`` endpoint requires authentication and
    expects the ``team_id`` as an additional argument.

    It can be reached at ``/team/vote/services?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": ("success", "failure"),
          "reason": string
        }

    :param int team_id: the id of the team voting.
    :param string service_1: the best service.
    :param string service_2: the second best service.
    :param string service_3: the third best service.

    :return: a JSON dictionary containing "success" or "failure", and, in case of failure, an explanation.
    """
    team_id = request.form.get("team_id")
    services = dict()
    services[request.form.get("service_1")] = 0
    services[request.form.get("service_2")] = 0
    services[request.form.get("service_3")] = 0

    cursor = mysql.cursor()
    for service_name in services.keys():
        try:
            cursor.execute("""SELECT id, team_id FROM services WHERE name=%s""", (service_name,))
            curr_row = cursor.fetchone()
            if curr_row is None:
                return json.dumps({"result": "failure", "reason": "unknown service %s" % service_name})
            if int(curr_row["team_id"]) == int(team_id):
                return json.dumps({"result": "failure", "reason": "cannot vote for own service"})

            services[service_name] = curr_row["id"]
        except Exception as e:
            return json.dumps({"result": "failure", "reason": str(e)})

    try:
        cursor.execute("""INSERT INTO vote_services (team_id, service_1, service_2, service_3)
                      VALUES(%s, %s, %s, %s)
                      ON DUPLICATE KEY UPDATE service_1=%s, service_2=%s, service_3=%s""",
                       (team_id,
                        services[request.form.get("service_1")],
                        services[request.form.get("service_2")],
                        services[request.form.get("service_3")],
                        services[request.form.get("service_1")],
                        services[request.form.get("service_2")],
                        services[request.form.get("service_3")]))
        mysql.database.commit()
    except Exception as e:
        return json.dumps({"result": "failure", "reason": str(e)})
    return json.dumps({"result": "success"})


@app.route("/team/dashboard/submit", methods=["POST"])
@requires_auth
def team_dashboard_submit():
    """The ``/team/dashboard/submit/`` endpoint requires authentication and
    expects the ``team_id`` as an additional argument.

    It can be reached at ``/team/dashboard/submit?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": ("success", "failure"),
          "reason": string
        }

    :param int team_id: the id of the team submitting the dashboard
    :param string name: the name of the dashboard
    :param string archive: the archive containing the dashboard (tar.gz in base64 encoding)

    :return: a JSON dictionary containing "success" or "failure", and, in case of failure, an explanation.
    """
    team_id = request.form.get("team_id")
    name = request.form.get("name")
    archive = request.form.get("archive")

    name = "".join([c for c in name if c in string.letters or c in string.whitespace])

    cursor = mysql.cursor()
    try:
        cursor.execute("""INSERT INTO dashboard_uploads (team_id, name, archive) VALUES(%s, %s, %s)""",
                       (team_id,
                        name,
                        archive))
        mysql.database.commit()
    except Exception as e:
        return json.dumps({"result": "failure", "reason": str(e)})
    return json.dumps({"result": "success"})

@app.route("/teams/token/info")
@requires_auth
def teams_token_info():
    """The ``/teams/info`` endpoint requires authentication.
    This endpoint fetches basic information about all the teams.

    It can be reached at ``/teams/info?secret=<API_SECRET>``.

    The JSON response is:

        {
            "teams":[
                        {
                        "id": int,
                        "name": string,
                        "instance_id": string,
                        "flag_token": "v6PHvAbpMrv1EcMpM5Xo25FNDuPoJ37v",
                        "login_token": "w3J0cNMv7UesPBB8da1F92I30y6v9z4a"
                        }, ..
                    ]
        }

    :return: a JSON dictionary containing basic information about all the teams.
    """
    cursor = mysql.cursor()

    cursor.execute("""SELECT teams.id, name, flag_token, login_token, ctf_key, root_key, ip, port
                        FROM teams, team_vm_key tvk 
                        WHERE teams.id = tvk.team_id """)
    teams = []
    for row in cursor.fetchall():
        team_id = row["id"]
        teams.append({"id": team_id,
                        "name": row['name'],
                        "instance_id": "team" + str(team_id),
                        "flag_token": row['flag_token'],
                        "login_token": row['login_token'],
                        "root_key": row['root_key'],
                        "ctf_key": row['ctf_key'],
                        "ip": row['ip'],
                        "port": row['port']
                      })

    return json.dumps({"teams": teams})

@app.route("/teams/info")
@requires_auth
def teams_info():
    """The ``/teams/info`` endpoint requires authentication.
    This endpoint fetches basic information about all the teams.

    It can be reached at ``/teams/info?secret=<API_SECRET>``.

    The JSON response is:

        {
            "teams":{team_id:
                            {
                            "id": int,
                            "name": string,
                            "url": string,
                            "country": string,
                            "validated": 0 or 1,
                            "academic_team": 0 or 1,
                            "email": string,
                            "academic_team": 0 or 1,
                            }, ..
                    }
        }

    :return: a JSON dictionary containing basic information about all the teams.
    """
    cursor = mysql.cursor()

    meta_map, extra_columns, join, where = {}, "", "", ""
    cursor.execute("""SELECT id, label
                        FROM team_metadata_labels""")
    for row in cursor.fetchall():
        meta_map[str(row["id"])] = row["label"]

    if meta_map:
        extra_columns = """, team_metadata_label_id as meta_id,
                             team_metadata.content as meta_content"""
        join = "JOIN team_metadata ON team_id = teams.id"
        ids = ", ".join(meta_map.keys())
        where = "WHERE team_metadata_label_id IN ({})".format(ids)

    cursor.execute("""SELECT teams.id, name, url, country, validated, academic_team,
                             email, logo {}
                        FROM teams {} {}""".format(extra_columns, join, where))
    teams = collections.defaultdict(lambda: collections.defaultdict(dict))
    for row in cursor.fetchall():
        team_id = row["id"]
        row["logo"] = str(row["logo"])

        if "meta_id" in row:
            row[meta_map[str(row["meta_id"])]] = row["meta_content"]
            del row["meta_id"], row["meta_content"]

        teams[team_id].update(row)

    return json.dumps({"teams": teams})


@app.route("/teams/publicinfo")
@requires_auth
def teams_publicinfo():
    """The ``/teams/publicinfo`` endpoint requires authentication.
    This endpoint fetches basic information about all the teams.

    It can be reached at ``/teams/publicinfo?secret=<API_SECRET>``.

    The JSON response is:

        {
            "teams": {
                      team_id: {
                                "id": int,
                                "name": string,
                                "url": string,
                                "country": string,
                                "logo": base64 encoded string,
                                ... public metadata ...
                                }, ..
                     }
        }

    :return: a JSON dictionary containing basic information about all the teams.
    """
    cursor = mysql.cursor()

    meta_map, extra_columns, join, where = {}, "", "", ""
    cursor.execute("""SELECT id, label
                        FROM team_metadata_labels
                       WHERE is_public = TRUE""")
    for row in cursor.fetchall():
        meta_map[str(row["id"])] = row["label"]

    if meta_map:
        extra_columns = """, team_metadata_label_id as meta_id,
                             team_metadata.content as meta_content"""
        join = "JOIN team_metadata ON team_id = teams.id"
        ids = ", ".join(meta_map.keys())
        where = "WHERE team_metadata_label_id IN ({})".format(ids)

    cursor.execute("""SELECT teams.id, name, url, country, validated, logo {}
                        FROM teams {} {}""".format(extra_columns, join, where))
    teams = collections.defaultdict(lambda: collections.defaultdict(dict))
    for row in cursor.fetchall():
        team_id = row["id"]
        row["logo"] = str(row["logo"])

        if "meta_id" in row:
            row[meta_map[str(row["meta_id"])]] = row["meta_content"]
            del row["meta_id"], row["meta_content"]

        teams[team_id].update(row)

    return json.dumps({"teams": teams})


#@app.route("/vpnconfig/set", methods=["POST"])
@app.route("/team/vpnconfig/set", methods=["POST"])
@requires_auth
def vpn_config_set():
    """The ``/team/vpnconfig/set`` endpoint
    requires authentication and expects the ``team_id`` and ``vpn_config`` as
    additional arguments. It is used to set the vpn information for a team id

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/team/vpnconfig/set?secret=<API_SECRET>``.

    The JSON response is::

        {
          "result": ("success", "failure")
        }

    :param int team_id: the ID of the team.
    :param str vpn_config: the vpn config information
    :return: a JSON dictionary confirming success
    """

    team_id = request.form.get("team_id")
    vpn_config = request.form.get("vpn_config")

    cursor = mysql.cursor()
    cursor.execute("""INSERT INTO vpn_info (team_id, vpn_config)
                      VALUES(%s, %s)
                      ON DUPLICATE KEY UPDATE vpn_config=%s""",
                   (team_id, vpn_config, vpn_config))
    mysql.database.commit()

    return json.dumps({"result": "success"})

#@app.route("/vpnconfig")
#@app.route("/vpnconfig/team/<int:team_id>")
@app.route("/teams/vpnconfig")
@app.route("/teams/vpnconfig/team/<int:team_id>")
@requires_auth
def vpn_config_get(team_id=None):
    """The ``/vpnconfig`` endpoint
    requires authentication and can filter by the ``team_id``
    It is used to retrieve the vpn information for a team id

    It can be reached at
    ``/teams/vpnconfig?secret=<API_SECRET>``
    ``/teams/vpnconfig/team/<team_id>?secret=<API_SECRET>``.

    The JSON response is::


        {"result" : [{
                     "team_id": int
                     "vpn_config": string
                    }]
        }

    :param int team_id: the ID of the team.
    :return: a json dictionary
    """

    cursor = mysql.cursor()

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

    base_query = "SELECT team_id, vpn_config FROM vpn_info"
    if filter_stmt:
        cursor.execute("{} WHERE {}".format(base_query, filter_stmt),
                       filter_values)
    else:
        cursor.execute(base_query)

    config_info = cursor.fetchall()

    return json.dumps({"result": config_info})


# Flag API endpoints
#
@app.route("/flag/generate/service/<int:service_id>/team/<int:team_id>",
           methods=["POST"])
@requires_auth
def flag_generate(team_id, service_id):
    """The ``/flag/generate/service/<service_id>/team/<team_id>`` endpoint
    requires authentication and expects the ``team_id`` and ``service_id`` as
    additional arguments. It is used to create a new flag for the specific
    service and team and store it in the database.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/flag/generate/service/<service_id>/team/<team_id>?secret=<API_SECRET>``.

    The JSON response is::

        {
          "id": int,
          "flag": string
        }

    :param int team_id: the ID of the team for which the flag will be created.
    :param int service_id: the ID of the service for which the flag will be
                           created.
    :return: a JSON dictionary containing the flag.
    """
    flag = _generate_new_flag()

    cursor = mysql.cursor()
    tick_id, _, _, _ = get_current_tick(cursor)
    cursor.execute("""INSERT INTO flags
                                  (team_id, service_id, flag, tick_id)
                      VALUES (%s, %s, %s, %s)""", (team_id, service_id, flag, tick_id))
    mysql.database.commit()
    id_ = cursor.lastrowid

    return json.dumps({"flag": flag,
                       "id": id_})


@app.route("/flag/set/<int:id>", methods=["POST"])
@requires_auth
def flag_set_cookie_and_flag_id(id):     # pylint: disable=C0103,W0622
    """The ``/flag/set/<id>`` endpoint requires authentication and expects the
    ``id`` of the flag as additional argument. It is used to associate a
    cookie and flag_id with an existing flag.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/flag/set/<id>?secret=<API_SECRET>``

    It expects the following inputs:

    - flag_id, the identifier that the setflag script has set.
    - cookie, the cookie that the setflag script has set.

    The JSON response is::

        {
          "id": int,
          "result": ("success", "failure")
        }

    :param int id: the id of flag for which flag_id and cookie should be set.
    :param str flag_id: the flag_id that identifies the flag.
    :param str cookie: the secret cookie that can be used to obtain the flag.
    :return: a JSON dictionary with a result status, to verify if setting the
             state was successful.
    """
    cookie = request.form.get("cookie")
    flag_id = request.form.get("flag_id")

    cursor = mysql.cursor()
    cursor.execute("""UPDATE flags SET flag_id = %s, cookie = %s
                      WHERE id = %s""",
                   (flag_id, cookie, id))
    mysql.database.commit()

    return json.dumps({"id": id,
                       "result": "success"})


#@app.route("/getlatestflagids")
@app.route("/flag/latest")
@requires_auth
def flag_get_latest_flag_ids():
    """The ``/flag/latest`` endpoint requires authentication and expects
    no other argument. It is used to retrieve the latest flag_ids for all
    services for all teams.

    It can be reached at ``/flag/latest?secret=<API_SECRET>``.

    The JSON response is::

        {
          "flag_ids" : { (team_id) : { (service_id) : (flag_id)} }
        }

    :return: a JSON dictionary containing a dictionary mapping team_ids to a
             dictionary mapping service_ids to flag_ids.
    """
    flag_ids = {}
    cursor = mysql.cursor()

    # Initialize flag_ids dict for each team_id
    cursor.execute("SELECT id FROM teams")
    for result in cursor.fetchall():
        team_id = result["id"]
        flag_ids[team_id] = {}

    # for each (team_id, service_id) pair get the flag_id of the most
    # recently created flag
    cursor.execute("""SELECT f.flag_id AS flag_id,
                             f.team_id AS team_id,
                             f.service_id AS service_id
                      FROM flags AS f
                      INNER JOIN (SELECT team_id, service_id,
                                  MAX(created_on) AS max_created_on
                                  FROM flags WHERE flag_id IS NOT NULL
                                  GROUP BY team_id, service_id)
                      AS grouped_flags
                      ON f.created_on = grouped_flags.max_created_on
                         AND f.team_id = grouped_flags.team_id
                         AND f.service_id = grouped_flags.service_id
                      WHERE f.flag_id IS NOT NULL""")

    for result in cursor.fetchall():
        service_id = result["service_id"]
        team_id = result["team_id"]
        flag_id = result["flag_id"]
        flag_ids[team_id][service_id] = flag_id

    return json.dumps({"flag_ids": flag_ids})


# pylint: disable=invalid-name
#@app.route("/getlatestflagandcookie/<int:team_id>/<int:service_id>")
@app.route("/flag/latest/team/<int:team_id>/service/<int:service_id>")
@requires_auth
def flag_latest_flag_id_and_cookie(team_id, service_id):
    """The ``/flag/latest/team/<team_id>/service/<service_id>`` endpoint
    requires authentication and expects the ``team_id`` and ``service_id`` as
    additional argument. It is used to retrieve the flag, flag_id, and cookie
    for the most recent flag for the specific service for the specific team.

    It can be reached at
    ``/flag/latest/team/<team_id>/service/<service_id>?secret=<API_SECRET>``.

    The JSON response is::

        {
          "id:": int,
          "flag": string,
          "cookie": string,
          "flag_id": string,
        }

    :param int team_id: the ID of the team for which the flag information
                        should be retrieved.
    :param int service_id: the ID of the service for which the flag
                           information should be retrieved.
    :return: a JSON dictionary containing the current flag and its associated
             flag_id and cookie.
    """
    cursor = mysql.cursor()
    cursor.execute("""SELECT id, flag, cookie, flag_id FROM flags
                      WHERE team_id = %s AND service_id = %s
                        AND flag_id IS NOT NULL AND cookie IS NOT NULL
                      ORDER BY created_on DESC LIMIT 1""",
                   (team_id, service_id))
    result = cursor.fetchone()
    if result is None:
        return json.dumps(dict())
    else:
        return json.dumps(result)
# pylint:enable=invalid-name


@app.route("/flag/submit", methods=["POST"])
@requires_auth
def flag_submit():
    """The ``/flag/submit`` endpoint requires authentication and expects no
    further arguments. It is used to submit a flag by the team identified by
    team_id.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/flag/submit?secret=<API_SECRET>``.

    It expects the following inputs:

    - team_id, the team that submitted the flag.
    - flag, the flag that is being submitted.
    - attack_up, whether the current game mode is attack-up or not.

    The JSON response is::

        {
          "id": int,
          "result": "correct" | "ownflag" (do you think this is defcon?)
                              | "incorrect"
                              | "alreadysubmitted"
                              | "notactive",
                              | "toomanyincorrect",
                              | "placetoolow", (only exists in the attack-up mode)
        }

    Here, ``notactive`` means that the flag was active, but it was not active
    in this tick, meaning the flag was submitted too late. For instance,
    because the flag associated with a wrong flag_id was submitted.

    The id has different meanings, depending on the result:

    - correct, ownflag, incorrect, notactive, the id of the submission.
    - alreadysubmitted, the id of the first submission.

    :param int team_id: the ID of the team that submitted the flag.
    :param str flag: the flag to be submitted.
    :param str attack_up: whether the current game mode is attack-up or not.
                          'true' means it's attack-up mode.
    :return: a JSON dictionary containing status information on the flag.
    """
    team_id = request.form.get("team_id")
    # Make sure team_id is an integer
    try:
        _ = int(team_id)
    except ValueError:
        return json.dumps({'error': 'Invalid Team ID.'})
    flag = request.form.get("flag")
    attack_up_str = request.form.get("attack_up", "")
    attack_up = True if attack_up_str.lower() == 'true' else False

    to_return = db_helpers.submit_flag(team_id, flag, attack_up, app.config["NUMBER_OF_TICKS_FLAG_VALID"])
    return json.dumps(to_return)

@app.route("/flag/submit_many", methods=["POST"])
@requires_auth
def flag_submit_many():
    """The ``/flag/submit_many`` endpoint requires authentication and expects no
    further arguments. It is used to submit flags by the team identified by
    team_id.

    Note that this endpoint requires a POST request.

    It can be reached at
    ``/flag/submit_many?secret=<API_SECRET>``.

    It expects the following inputs as a json object:

    - team_id, the team that submitted the flag.
    - flags, the flags that are being submitted.
    - attack_up, whether the current game mode is attack-up or not.

    The JSON response is::
    [
        {
          "id": int,
          "result": "correct" | "ownflag" (do you think this is defcon?)
                              | "incorrect"
                              | "alreadysubmitted"
                              | "notactive",
                              | "toomanyincorrect",
                              | "placetoolow", (only exists in the attack-up mode)
        }
    ]
    Here, ``notactive`` means that the flag was active, but it was not active
    in this tick, meaning the flag was submitted too late. For instance,
    because the flag associated with a wrong flag_id was submitted.

    The id has different meanings, depending on the result:

    - correct, ownflag, incorrect, notactive, the id of the submission.
    - alreadysubmitted, the id of the first submission.
    """
    info_submission = request.get_json()

    team_id = info_submission['team_id']
    if type(team_id) not in {int, long}:
        return json.dumps({'error': 'Invalid Team ID.'})

    flags = info_submission['submitted_flags']
    attack_up_str = info_submission.get("attack_up", '')
    attack_up = True if attack_up_str.lower() == 'true' else False

    result = []
    for cur_flag in flags:
        submission_result = db_helpers.submit_flag(
            team_id,
            cur_flag,
            attack_up,
            app.config["MAX_INCORRECT_FLAGS_PER_TICK"],
            app.config["NUMBER_OF_TICKS_FLAG_VALID"],
            app.config["ATTACKUP_HEAD_BUCKET_SIZE"]
        )
        result.append(submission_result)

    return json.dumps(result)

