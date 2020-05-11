#!/bin/bash

/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/syslog.conf  &
python3 scriptbot.py