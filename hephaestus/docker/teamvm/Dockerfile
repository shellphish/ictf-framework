FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade && \
    apt-get update -y && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible && \
    apt-get -y update && apt-get -y install ansible

RUN useradd -m --uid 31337 ctf

COPY ./game_config.json /root/game_config.json
COPY ./teamvms/provisioning /root/provisioning
COPY ./teamvms/bundled_services /opt/ictf/services
COPY ./common/hephaestus_provisioning/teamhosts /root/teamhosts
COPY ./teamvms/start.sh /root/start.sh

ARG services

# RUN ansible-playbook /root/provisioning/hephaestus_provisioning/ansible/ansible-provisioning.yml --extra-vars="$services" && chmod +x /root/start.sh
RUN echo "localhost ansible_connection=local" > /etc/ansible/hosts && \
    ansible-playbook /root/provisioning/hephaestus_provisioning/ansible/ansible-provisioning.yml \
        --extra-vars="$services" \
        --extra-vars="BASE=1" \
        --extra-vars="PRIMER=1" \
        --extra-vars="LOCAL=True" \
        --extra-vars="GAME_CONFIG_PATH=/root/game_config.json" \
        && \
    chmod +x /root/start.sh 
