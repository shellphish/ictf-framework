#!/bin/bash

#
# This script starts up forwarding and does some randomization on traffic.
#

echo "Enabling IPv4 forwarding"
sysctl -w net.ipv4.ip_forward=1

for ${TEAM} in ${TEAMS}; do
    route add 10.7.${TEAM}.2 dev eth1
    iptables -t nat -A POSTROUTING -d 10.7.${TEAM}.0/24 -j SNAT --to-source 10.7.253.1-10.7.253.255
done
