#!/bin/bash

cat /root/teamhosts >> /etc/hosts

service openvpn start

tail -f /dev/null