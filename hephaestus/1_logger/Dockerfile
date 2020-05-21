
FROM ubuntu:18.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade && \
    apt-get update -y && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible && \
    apt-get -y update && apt -y install ansible git wget curl vim iputils-ping python-pip python-dev python3-dev build-essential htop

COPY ./secrets /opt/ictf/secrets
COPY ./logger /opt/ictf/logger

WORKDIR /opt/ictf/logger

#RUN pip install --upgrade pip && pip install -r requirements2.txt

RUN ansible-playbook provisioning/hephaestus_provisioning/ansible-provisioning.yml --become --extra-vars ICTF_USER="root"  --extra-vars ICTF_FRAMEWORK_DIR_HOST="/opt/ictf"

RUN chmod +x ./start.sh

ENTRYPOINT ./start.sh