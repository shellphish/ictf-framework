FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nginx uwsgi uwsgi-plugin-python mysql-server python-pip python-virtualenv python-mysqldb python-dev awscli openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre
RUN pip install --upgrade pip setuptools pyOpenSSL ndg-httpsclient pyasn1

COPY ./database /opt/ictf/database
COPY ./scoring_ictf /opt/ictf/scoring_ictf

WORKDIR /opt/ictf/database

RUN chmod +x ./start.sh && ansible-playbook ./provisioning/hephaestus_provisioning/ansible-provisioning.yml

ENTRYPOINT ./start.sh