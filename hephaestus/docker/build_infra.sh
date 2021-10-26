#!/bin/bash
set -euo

docker-compose -f ./docker-compose-base.yml build $@
docker-compose -f ./docker-compose-infra.yml build --parallel $@
./build_teamvm.py ../../game_config.json
