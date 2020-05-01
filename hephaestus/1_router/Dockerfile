FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y iptraf python-pip python-dev python3-dev build-essential awscli iptables-persistent iftop libcurl4-openssl-dev libssl-dev python-apt zip unzip

COPY ./router /opt/ictf/router
COPY ./common/teamhosts /etc/hosts
COPY ./hephaestus/vpnkeys/openvpn.zip /opt/ictf/openvpn.zip

WORKDIR /opt/ictf/router

RUN pip install --upgrade pip && pip install -r requirements2.txt

RUN ansible-playbook provisioning/ansible-provisioning.yml --become --extra-vars ICTF_USER="hacker" 

RUN chmod +x ./start.sh

ENTRYPOINT ./start.sh