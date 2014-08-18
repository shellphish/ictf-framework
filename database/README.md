# The Database and Gamebot

## Database

The database is the central point for all other parts of the ctf
system. An HTTP REST-style interface sits inbetween the actual
database and the other components. This HTTP API allows all the other
components to report on the state of the game or query the state of
the game. The API documentation is contained in
templates/homescreen.html.

### Import Files

- ctf-database.conf: This file has the upstart script for the database
  API service

- database.sql: A SQL file to start a blank DB (but still not ready
  for game-time).
- database_service.py: The HTTP REST-like API. It uses Flask. Has been
  used the past three iCTFs, so it could use a clean-up.
- database_tornado.py: A separate script to run the database API
  through tornado, which gives much better performance.
- flaskext/mysql.py: A tweak to the flaskext.mysql package to get
  hashes back from the DB instead of tuples.
- gamebot.conf: Upstart script to run the gamebot.
- gamebot.py: Responsible for progressing the game.
- reset_db.py: The scripts which resets the database based on the
  number of teams and which services are included in this competition.
  Reads the service info from /opt/database/combined_info.json on the
  organization VM.
- settings.py: Has the DB connection info.
- templates/homescreen.html: The documentation for the database API.

## Gamebot

The gamebot is responsible for progressing the game (each "round" of
the game is known as a tick). Every tick the gamebot decides which
scripts to run against which team and randomizes the order. This
information is persisted directly into the database, then the gamebot
sleeps until the next tick.
