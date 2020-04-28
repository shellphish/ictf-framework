FROM ictf_2_melt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y iptraf python-pip python-dev python3-dev build-essential awscli iptables-persistent iftop libcurl4-openssl-dev libssl-dev python-apt

COPY ./router /opt/ictf/router
COPY ./secrets /opt/ictf/secrets
COPY ./common/teamhosts /etc/hosts

WORKDIR /opt/ictf/router

RUN pip install --upgrade pip && pip install -r requirements2.txt

RUN ansible-playbook --become --extra-vars ICTF_USER="hacker" provisioning/building_time/ansible/main.yml