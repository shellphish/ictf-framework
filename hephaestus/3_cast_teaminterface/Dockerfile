FROM ictf_2_melt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python-pip python-virtualenv python-dev libjpeg8 libjpeg-dev zlib1g zlib1g-dev libpng-dev libmemcached-dev libmemcached-tools libgeoip1 libgeoip-dev geoip-bin geoip-database redis-server

COPY ./teaminterface /opt/ictf/teaminterface
COPY ./secrets /opt/ictf/secrets

WORKDIR /opt/ictf/teaminterface

RUN pip install -r requirements.txt

RUN ansible-playbook --become --extra-vars ICTF_USER="hacker" provisioning/building_time/ansible/main.yml