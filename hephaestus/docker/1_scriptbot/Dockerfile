FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python3-pip python3-virtualenv python3 python3-dev git libssl-dev libffi-dev build-essential libc6-dev-i386

COPY ./scriptbot /opt/ictf/scriptbot

WORKDIR /opt/ictf/scriptbot

COPY ./common/hephaestus_provisioning/teamhosts ./teamhosts

RUN pip3 install -r requirements.txt

RUN ansible-playbook provisioning/hephaestus_provisioning/ansible-provisioning.yml

RUN chmod +x ./start.sh && chmod +x ./start_idle_mode.sh

ENTRYPOINT ./start.sh
