#!/bin/bash

# Hack to differentiate local testing to remote games
if [ "$IS_LOCAL_REGISTRY" == 1 ]; then
    echo "Starting local game... setting uip gateway"
    ip route add 10.9.0.0/16 via 172.31.172.1 dev eth0
fi

cat ./teamhosts >> /etc/hosts

service prometheus-node-exporter start

/usr/share/logstash/bin/logstash -f /etc/logstash/conf.d/syslog.conf  &

python3 scriptbot.py
