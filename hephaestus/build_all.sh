#!/bin/bash

# docker-compose does not handle dependency at building time so we need to use
# this workaround in order to use parallel build without breaking ther dependecy
# graph
docker-compose -f ./docker-compose-base.yml build heat
docker-compose -f ./docker-compose-base.yml build melt

docker-compose -f ./docker-compose-cast.yml build --parallel

docker-compose -f ./docker-compose-harden.yml build --parallel
