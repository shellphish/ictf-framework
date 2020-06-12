FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nginx uwsgi uwsgi-plugin-python mysql-server python-pip python-virtualenv python-mysqldb python-dev 
RUN pip install --upgrade pip pyOpenSSL ndg-httpsclient pyasn1

COPY ./database /opt/ictf/database
COPY ./scoring_ictf /opt/ictf/scoring_ictf

WORKDIR /opt/ictf/database

RUN chmod +x ./start.sh && ansible-playbook ./provisioning/hephaestus_provisioning/ansible-provisioning.yml

ENTRYPOINT ./start.sh