#!/bin/bash

# This script enables forwarding on your box and installs the VPN bundle that
# you got from the organizers. After installing, your box routes your requests
# to the vulnerable boxes.

apt-get -y install openvpn

echo "Enabling IPv4 forwarding"
sysctl -w net.ipv4.ip_forward=1

tar -xf team${TEAMID}.tgz -C /etc/openvpn/

service openvpn restart ${TEAMID}
