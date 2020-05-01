#!/bin/bash

service openvpn start

python ictf-tcpdump.py &

python ictf-pcap-s3.py 