#!/bin/bash

# Exits if any command exits with non-zero status
set -euo pipefail

# Ensures that secrets were already generated
if [ ! -d ./secrets ]; then
    echo -e '\e[31mERROR\e[0m: You must first generate secrets. Try ./make_secrets.sh' 1>&2;
    exit 1;
fi

echo 'Adjusting max memory for elasticsearch, unfortunately for a local deploy we have to do this outside of docker for now'
sudo sysctl -w vm.max_map_count=262144

echo build_infra
echo "`date` | starting build_infra" >> logs_build_infra.txt
(cd ./hephaestus/docker && ./build_infra.sh && cd -) | tee -a logs_build_infra.txt

echo deploy_infra
echo "`date` | starting deploy_infra" >> logs_deploy_infra.txt
(cd ./ares/docker && ./deploy_infra.py ../../game_config.json ../../secrets && cd ../../) | tee -a logs_deploy_infra.txt
 
echo compose down
cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml down -v --remove-orphans && cd ../../
 
echo compose up
cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml up -d && cd ../../

sleep 5;
echo "Registering teams and services"
echo "`date` | starting deploy_infra" >> logs_register_teams_services.txt
(cd ./ares/docker && ./register_services_and_teams.sh ../../game_config.json && cd -) | tee -a logs_register_teams_services.txt
# start game: http://localhost:5000/game/insert?secret=JPG1pD8Zr2rT5fjgY_D_MyJPY
