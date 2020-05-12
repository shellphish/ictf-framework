#!/bin/bash

service mysql start
service nginx start

# TO FIX, REGISTER AS SERVICE PLZ.
/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/syslog.conf  &

# Register logstash
#update-rc.d logstash defaults 95 10
#service logstash start 

ICTF_DATABASE_SETTINGS=/opt/ictf/settings/database-api.py  /usr/bin/uwsgi -c uwsgi.ini &

/opt/ictf/venv/database/bin/python ictf-db-export-s3.py
