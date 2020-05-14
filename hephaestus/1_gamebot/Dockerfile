FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip ansible openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre

COPY ./gamebot /opt/ictf/gamebot

WORKDIR /opt/ictf/gamebot

RUN pip install -r requirements.txt

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/ansible-provisioning.yml --extra-vars ICTF_API_ADDRESS="database.ictf" 

ENTRYPOINT ./start.sh