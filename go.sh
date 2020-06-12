cd ./hephaestus && ./build_infra.sh && cd /home/degrigis/projects/ictf/ictf-framework-3.0 



cd ./ares/docker && ./deploy_infra.py /home/degrigis/projects/ictf/ictf-framework-3.0/game_config.json /home/degrigis/projects/ictf/ictf-framework-3.0/secrets && cd /home/degrigis/projects/ictf/ictf-framework-3.0 
 
cd ./ares/docker &&  docker-compose -f docker-compose-local.generated.yml down -v --remove-orphans && cd /home/degrigis/projects/ictf/ictf-framework-3.0
 

cd ./ares/docker && docker-compose -f docker-compose-local.generated.yml up && cd /home/degrigis/projects/ictf/ictf-framework-3.0
