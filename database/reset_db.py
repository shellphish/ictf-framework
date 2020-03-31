#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Resets the database
"""

from __future__ import print_function

import random

from api import mysql


# Helper functions
#
def _init_database():
    """Initialze the database tables"""

    database = mysql.connect()
    cursor = database.cursor(raw=True, buffered=False)

    # Wipe the database and setup new one
    with open("/home/ictf/ictf-framework/database/support/database.sql", "r") as file_:
        setup_script = file_.read()

    # The library returns a generator for each statement, we need to eval all
    # of them.
    list(cursor.execute(setup_script, multi=True))

    # Create the game
    game_id = random.randint(0, 1000000)
    cursor.execute("INSERT INTO game (id) VALUES (%s)", (game_id,))

    database.commit()


def main():     # pylint:disable=missing-docstring
    _init_database()

if __name__ == "__main__":
    main()
