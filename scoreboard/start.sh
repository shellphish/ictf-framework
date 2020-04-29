#!/bin/bash

service nginx start

service redis-server start

ulimit -n 20000
# sysctl -w net.core.somaxconn="20000"

python poller.py config.json >> poller.logs &

gunicorn --log-file /var/log/gunicorn/glog.log -k gevent --worker-connections 10000 -w 30 --bind unix:/opt/ictf/scoreboard/gunicorn.sock app:app