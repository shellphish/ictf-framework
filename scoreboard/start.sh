#!/bin/bash

service nginx start
service prometheus-node-exporter start
service redis-server start

ulimit -n 20000
# sysctl -w net.core.somaxconn="20000"

/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/syslog.conf  &

python poller.py config.json >> poller.logs &

gunicorn --log-file /var/log/gunicorn/glog.log -k gevent --worker-connections 10000 -w 30 --bind unix:/opt/ictf/scoreboard/gunicorn.sock app:app