FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends iptraf python-pip python-dev python3-dev build-essential awscli iptables-persistent iftop libcurl4-openssl-dev libssl-dev python-apt zip unzip openvpn python-wheel

COPY ./router /opt/ictf/router

WORKDIR /opt/ictf/router

RUN pip install --upgrade pip && pip install -r requirements2.txt

RUN ansible-playbook provisioning/hephaestus_provisioning/ansible-provisioning.yml --become 

RUN chmod +x ./start.sh

ENTRYPOINT ./start.sh