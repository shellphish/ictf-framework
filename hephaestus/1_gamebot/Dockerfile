FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip 

COPY ./gamebot /opt/ictf/gamebot

WORKDIR /opt/ictf/gamebot

RUN pip install -r requirements.txt

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/ansible-provisioning.yml --extra-vars ICTF_API_ADDRESS="database" 

ENTRYPOINT ./start.sh