#!/bin/bash

echo build_infra
cd ./hephaestus/docker && ./build_infra.sh && cd - 


echo deploy_infra
cd ./ares/docker && ./deploy_infra.py ../../game_config.json ../../secrets && cd ../../
 
echo compose down
cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml down -v --remove-orphans && cd ../../
 
echo compose up
cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml up && cd ../../
