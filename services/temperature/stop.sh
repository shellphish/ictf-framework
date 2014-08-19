#!/bin/bash
cd /var/ictf/services/temperature
pkill -u temperature
sleep 1
pkill -KILL -u temperature
