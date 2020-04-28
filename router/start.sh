#!/bin/bash

service openvpn restart

python ictf-tcpdump.py &

python ictf-pcap-s3.py 