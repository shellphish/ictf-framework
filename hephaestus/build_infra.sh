#!/bin/bash

docker-compose -f ./docker-compose-base.yml build $@
docker-compose -f ./docker-compose-infra.yml build --parallel $@
