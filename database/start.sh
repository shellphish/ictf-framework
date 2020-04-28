#!/bin/bash

service mysql restart

service nginx restart

ICTF_DATABASE_SETTINGS=/opt/ictf/settings/database-api.py  /usr/bin/uwsgi -c uwsgi.ini &

/opt/ictf/venv/database/bin/python ictf-db-export-s3.py
