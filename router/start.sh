#!/bin/bash

iptables-restore < ./provisioning/hephaestus_provisioning/iptables_rules

unzip -d /etc/openvpn/ /etc/openvpn/openvpn.zip

service openvpn start

python3 ictf-tcpdump.py &

python3 ictf-pcap-s3.py
