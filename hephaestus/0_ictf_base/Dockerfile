FROM ubuntu:16.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade && \
    apt-get update -y && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible && \
    apt-get -y update && apt-get -y install ansible 

COPY ./secrets /opt/ictf/secrets
COPY ./ictf-base/provisioning/ansible-provisioning.yml /root

RUN ansible-playbook /root/ansible-provisioning.yml
