#!/bin/bash

iptables-restore < ./provisioning/hephaestus_provisioning/iptables_rules

unzip -d /etc/openvpn/ /etc/openvpn/openvpn.zip

service openvpn start

python ictf-tcpdump.py &

python ictf-pcap-s3.py 