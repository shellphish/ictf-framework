FROM ictf_3_cast_gamebot

WORKDIR /opt/ictf/gamebot

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/terraform_provisioning.yml --extra-vars ICTF_API_ADDRESS="database" 

ENTRYPOINT ./start.sh