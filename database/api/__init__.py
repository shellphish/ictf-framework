#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

"""The database is the central point for all other parts of the CTF framework.
It is a HTTP REST interface that sits between the actual MySQL database and
the other components. It allows all other components to report on the state of
the game or query the state of the game.

The database API follows some basic design guidelines:

- Every endpoint that modifies the state of the database is a POST request.
- Every endpoint that only serves data but does not modify anything is a GET
  request.
- If multiple parameters can be passed to an endpoint, they are (generally) in
  alphabetical order. In some cases, the name of the parameter is omitted
  because the association is clear, e.g., we use
  ``/service/state/set/<service_id>`` instead of
  ``/servce/state/set/service/<service_id>``.
"""

__authors__ = "Adam Doupé, Kevin Borgolte, Giovanni Vigna, Chris Salls"
__version__ = "0.1.1"

from flask import Flask
from .flaskext.mysql import MySQL

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


# Initialize Flask and MySQL wrapper
#
# pylint:disable=invalid-name
app = Flask(__name__)
app.config.from_envvar("ICTF_DATABASE_SETTINGS")

mysql = MySQL(app)
# pylint:enable=invalid-name

@app.route("/ping")
def ping():
    return "pong"

# The following files contain subset of the routes
# that are specific to a subset of the functionality


from . import brand_new_scoring
from . import db_helpers
from . import scored_events
from . import scores
from . import scripts
from . import services
from . import teams
from . import general
from . import uploads
from . import ticket

if __name__ == "__main__":
    app.run()
