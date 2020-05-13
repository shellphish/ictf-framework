#!/bin/bash

GAME_CONFIG_PATH=$1

python ../../database/provisioning/create_teams.py 127.0.0.1:5000 $GAME_CONFIG_PATH
# python ../../database/provisioning/create_services.py 127.0.0.1:5000 $GAME_CONFIG_PATH
