FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-pip python3-wheel

COPY ./gamebot /opt/ictf/gamebot

WORKDIR /opt/ictf/gamebot

RUN pip install -r requirements.txt

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/hephaestus_provisioning/ansible-provisioning.yml --extra-vars ICTF_API_ADDRESS="database.ictf" 

ENTRYPOINT ./start.sh
