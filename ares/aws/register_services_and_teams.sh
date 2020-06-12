#!/bin/bash

set -x

DATABASE_IP=$1
GAME_CONFIG_PATH=$2

python3 ../../database/provisioning/create_teams.py "$DATABASE_IP" "$GAME_CONFIG_PATH"
python3 ../../database/provisioning/create_services.py "$DATABASE_IP" "$GAME_CONFIG_PATH"
