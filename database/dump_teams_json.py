#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import mysql.connector

db_pass = open('/opt/ictf/secrets/database-api/mysql', "r").read().rstrip()
conn = mysql.connector.connect(user='ictf', password=db_pass, database='ictf',
                               unix_socket='/var/run/mysqld/mysqld.sock',
                               get_warnings=True,
                               raise_on_warnings=True)  # pylint:disable=star-args
cursor = conn.cursor(dictionary=True)

cursor.execute("SELECT teams.id, name, url, country, logo, email, flag_token, login_token, root_key, ctf_key, ip, port FROM teams JOIN team_vm_key ON teams.id=team_vm_key.team_id")

teams = {}
vals = cursor.fetchall()
for row in vals:
    team_id = row["id"]
    row["logo"] = str(row["logo"])

    teams["team" + str(team_id)] = row

with open('/opt/ictf/database/team_info.json', 'w+') as fp:
    json.dump({"teams": teams}, fp, indent=2)

conn.close()








