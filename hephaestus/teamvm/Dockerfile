FROM ubuntu:18.04

ARG SERVICES

RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && \
    apt-get install -y zip tmux screen vim emacs nano curl wget python2.7 python3 python-pip python3-pip ruby perl gcc binutils build-essential tcpdump docker.io ansible

RUN useradd -m --uid 31337 ctf

COPY ./teamvms/provisioning /root/provisioning
COPY ./teamvms/bundled_services /opt/ictf/services

# RUN ansible-playbook /root/provisioning/ansible/ansible-provisioning.yml --extra-vars=$SERVICE