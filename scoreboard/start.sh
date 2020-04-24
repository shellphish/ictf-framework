#!/bin/bash

service nginx start

./bin/run_app.sh &

python poller.py config.json