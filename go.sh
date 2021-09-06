#!/bin/bash

set -euo pipefail
# ensure that secrets were already generated

if [ ! -d ./secrets ]; then
    echo -e '\e[31mERROR\e[0m: You must first generate secrets. Try ./make_secrets.sh' 1>&2;
    exit 1;
fi;

echo build_infra
cd ./hephaestus/docker && ./build_infra.sh && cd - 

echo 'Adjusting max memory for elasticsearch'
sudo sysctl -w vm.max_map_count=262144

echo deploy_infra
cd ./ares/docker && ./deploy_infra.py ../../game_config.json ../../secrets && cd ../../
 
echo compose down
cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml down -v --remove-orphans && cd ../../
 
echo compose up
cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml up -d && cd ../../
# start game: http://localhost:5000/game/insert?secret=JPG1pD8Zr2rT5fjgY_D_MyJPY
