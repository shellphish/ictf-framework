#!/bin/bash

/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/syslog.conf  &

service prometheus-node-exporter start
service nginx start
# TODO: Investigate what's the impact of the removed performance tweaks (Listen queue size is greater than the system max net.core.somaxconn (128))
# uwsgi -s /tmp/ictf-api.sock --chmod-socket --logto /tmp/uwsgi.log --module team_interface --callable app --enable-threads -z 6000 --master --listen 65535 --processes 10 --max-requests 655350 --die-on-term
uwsgi -c uwsgi.ini --enable-threads -z 6000 --die-on-term
