#!/bin/bash

# This script enables forwarding on your box and installs the VPN bundle that
# you got from the organizers. After installing, your box routes your requests
# to the vulnerable boxes.

apt-get -y install openvpn

tar -xf team${TEAMID}.tgz -C /etc/openvpn/

service openvpn restart ${TEAMID}

source $(dirname $0)/start.sh
