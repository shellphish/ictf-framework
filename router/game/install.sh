#!/bin/bash

# This script setups the VPN concentrator VM to route traffic to the vulnerable
# boxes.

apt-get -y install openvpn

echo "Enabling IPv4 forwarding"
sysctl -w net.ipv4.ip_forward=1

tar -xf concentrator.tgz -C /etc/openvpn/

service openvpn restart ictf-in-a-box

for ${TEAM} in ${TEAMS}; do
    route add 10.7.${TEAM}.2 dev eth1
done
