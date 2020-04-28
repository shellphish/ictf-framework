FROM ictf_3_cast_gamebot

COPY ./gamebot /opt/ictf/gamebot

WORKDIR /opt/ictf/gamebot

RUN pip install -r requirements.txt

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/ansible-provisioning.yml --extra-vars ICTF_API_ADDRESS="database" 

ENTRYPOINT ./start.sh