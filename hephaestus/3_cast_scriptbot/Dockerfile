FROM ictf_2_melt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-virtualenv python2.7 python-dev git libssl-dev libffi-dev build-essential libc6-dev-i386 docker.io

COPY ./scriptbot /opt/ictf/scriptbot
COPY ./secrets /opt/ictf/secrets
COPY ./common/teamhosts /etc/hosts

WORKDIR /opt/ictf/scriptbot

RUN pip install -r requirements.txt

# RUN ansible-playbook --become --extra-vars ICTF_USER="hacker" provisioning/building_time/ansible/main.yml