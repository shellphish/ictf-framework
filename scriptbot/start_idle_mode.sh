#!/bin/bash

ip route add 10.9.0.0/16 via 172.31.172.1 dev eth0

cat ./teamhosts >> /etc/hosts

tail -f /dev/null