FROM ictf_2_melt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip 

COPY ./gamebot /opt/ictf/gamebot

WORKDIR /opt/ictf/gamebot

RUN pip install -r requirements.txt

# RUN ansible-playbook --become --extra-vars ICTF_USER="hacker" provisioning/building_time/ansible/main.yml