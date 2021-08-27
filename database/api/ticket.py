#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from flask import request, abort, jsonify

from . import app, mysql
from .utils import requires_auth


@requires_auth
@app.route("/tickets/add", methods=['POST'])
def submit_ticket():
    team_id = request.form.get("team_id")
    subject = request.form.get("subject")
    msg = request.form.get("message")
    ts = request.form.get("ts")
    cursor = mysql.cursor()

    cursor.execute("""INSERT INTO tickets
                          (team_id, ts, subject, msg, response)
                      VALUES (%s, %s, %s, %s, %s)""",
                   (team_id, ts, subject, msg, "No Response Yet"))
    ticket_id = cursor.lastrowid

    mysql.database.commit()

    if cursor.rowcount == 0:
        return json.dumps({"result": "fail"})
    else:
        return json.dumps({"result": "success", "ticket_id": ticket_id})


@app.route("/tickets/get")
@app.route("/tickets/get/<int:team_id>")
@requires_auth
def get_all_tickets(team_id = None):
    cursor = mysql.cursor()
    if not team_id:
        cursor.execute("""SELECT * FROM tickets""")
    else:
        cursor.execute("""SELECT * FROM tickets where team_id = %d;""", team_id)
    tks = cursor.fetchall()
    for t in tks:
        t['msg'] = t['msg'].decode('utf-8')
        t['response'] = t['response'].decode('utf-8')
    return jsonify({"tickets": tks})


@app.route("/tickets/get/open")
@requires_auth
def get_open_tickets():
    cursor = mysql.cursor()

    cursor.execute("""SELECT * FROM tickets WHERE done = 0;""")
    return jsonify({"tickets": cursor.fetchall()})

@app.route("/tickets/respond/<int:ticket_id>")
@requires_auth
def respond_to_ticket(ticket_id):
    response = request.form.get("response")
    cursor = mysql.cursor()

    cursor.execute("""UPDATE tickets SET response = %s WHERE id = %s;""", (response, ticket_id))
    mysql.database.commit()

    return jsonify({"result": 'success'})


@app.route("/tickets/close/<int:ticket_id>", methods=['POST'])
@requires_auth
def close_ticket(ticket_id):
    ticket_id = int(ticket_id)
    cursor = mysql.cursor()
    cursor.execute("""UPDATE tickets SET done = 1 WHERE id = %s;""", ticket_id)
    mysql.database.commit()
    return json.dumps({"result": 'success'})

