#!/bin/bash
cd /var/ictf/services/poipoi
pkill -u poipoi
rm -f poi.dat
rm -f user.dat
sleep 1
pkill -KILL -u poipoi

