FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python-virtualenv python2.7 python3 python-dev git libssl-dev libffi-dev build-essential libc6-dev-i386 docker.io && \
                     apt-get -y install ansible openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre

COPY ./scriptbot /opt/ictf/scriptbot
COPY ./common/teamhosts /etc/hosts

WORKDIR /opt/ictf/scriptbot

RUN pip3 install -r requirements.txt

RUN ansible-playbook provisioning/hephaestus_provisioning/ansible-provisioning.yml

RUN chmod +x ./start.sh 

ENTRYPOINT ./start.sh