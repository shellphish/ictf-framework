FROM ictf_2_melt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nginx uwsgi uwsgi-plugin-python mysql-server python-pip python-virtualenv python-mysqldb python-dev awscli

RUN pip install --upgrade pip setuptools pyOpenSSL ndg-httpsclient pyasn1

COPY ./database /opt/ictf/database
COPY ./scoring_ictf /opt/ictf/scoring_ictf

WORKDIR /opt/ictf/database

# RUN service mysql start && ansible-playbook --become --extra-vars ICTF_USER="hacker" provisioning/building_time/ansible/main.yml