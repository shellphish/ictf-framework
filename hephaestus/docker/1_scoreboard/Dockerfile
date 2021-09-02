FROM ictf_base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y nginx git redis-server build-essential
RUN apt-get update && apt-get install -y sudo uwsgi daemon

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get update && apt-get install -y nodejs
RUN apt-get update && apt-get install -y python3-pip python3-virtualenv python3-dev uwsgi-plugin-python3 python3-setuptools python3-wheel
#RUN pip install --upgrade pip
#RUN pip --version 

COPY ./scoreboard /opt/ictf/scoreboard

WORKDIR /opt/ictf/scoreboard

RUN pip install -r requirements.txt

RUN ansible-playbook provisioning/hephaestus_provisioning/ansible-provisioning.yml --become --extra-vars ICTF_USER="root" --extra-vars ICTF_FRAMEWORK_DIR_HOST="/opt/ictf"  --extra-vars ICTF_API_ADDRESS="database.ictf"

RUN chmod +x ./start.sh

ENTRYPOINT ./start.sh
