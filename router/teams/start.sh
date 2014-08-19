#!/bin/bash

#
# This script starts up forwarding.
#

echo "Enabling IPv4 forwarding"
sysctl -w net.ipv4.ip_forward=1
