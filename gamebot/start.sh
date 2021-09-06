#!/bin/bash

service prometheus-node-exporter start

/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/syslog.conf  &
python3 gamebot.py
