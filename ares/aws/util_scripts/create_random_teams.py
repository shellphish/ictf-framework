#!/usr/bin/env python

import sys
import json
import hashlib

with open(sys.argv[1], 'r') as f:
    d = json.load(f)

teams = []
teams.append({
        "name": "Shellphish",
        "url": "-",
        "country": "USA",
        "logo": "",
        "email": "shellphish@pineapple.on.pizza",
        "validated": 1,
        "academic_team": 1,
        "id": 1,
        "flag_token": "aaaaaaaaaaaaaaaaaaaa",
        "organizer_hosted": True
    })

for team_id in range(2, int(sys.argv[2])+1):
    t = dict(teams[-1])
    t['name'] = 'COGLIONI{}'.format(team_id)
    t['id'] = team_id
    t['flag_token'] = hashlib.md5(t['name'].encode()).hexdigest()[:20]
    t['email'] = t['name'].lower() + "@pineapple.on.pizza"
    t['organizer_hosted'] = True
    teams.append(t)

d['teams'] = teams
with open(sys.argv[1], 'w') as f:
    json.dump(d, f, indent=2)
