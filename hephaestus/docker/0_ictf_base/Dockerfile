FROM ubuntu:20.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade && \
    apt-get update -y && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible && \
    apt-get -y update && apt-get -y install ansible net-tools iputils-ping

RUN apt-get -y install --only-upgrade python3 python3.8
# RUN update-alternatives  --set python3 /usr/bin/python3.8

COPY ./secrets /opt/ictf/secrets
COPY ./ictf-base/provisioning/ansible-provisioning.yml /root
COPY ./ictf-base/provisioning/requirements-ansible-roles.yml /tmp

RUN ansible-playbook /root/ansible-provisioning.yml
