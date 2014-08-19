#!/bin/bash

# This script setups the VPN concentrator VM to route traffic to the vulnerable
# boxes.

apt-get -y install openvpn

tar -xf concentrator.tgz -C /etc/openvpn/

service openvpn restart ictf-in-a-box

source $(dirname $0)/start.sh
