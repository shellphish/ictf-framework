FROM ubuntu:16.04

RUN DEBIAN_FRONTEND=noninteractive apt-get -y --no-install-recommends -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade && \
    apt-get update -y && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible && \
    apt-get -y update && apt -y install ansible git wget curl vim iputils-ping

COPY ./secrets /opt/ictf/secrets
