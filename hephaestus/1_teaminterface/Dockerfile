FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nginx python-pip python-virtualenv python-dev libjpeg8 libjpeg-dev zlib1g zlib1g-dev libpng-dev libmemcached-dev libmemcached-tools libgeoip1 libgeoip-dev geoip-bin geoip-database redis-server openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre

COPY ./teaminterface /opt/ictf/teaminterface

WORKDIR /opt/ictf/teaminterface

RUN pip install -r requirements.txt

RUN ansible-playbook provisioning/ansible-provisioning.yml --become --extra-vars ICTF_USER="hacker"  --extra-vars ICTF_DB_API_ADDRESS="database"

RUN chmod +x ./start.sh 

ENTRYPOINT ./start.sh