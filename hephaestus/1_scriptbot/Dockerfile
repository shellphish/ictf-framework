FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-virtualenv python2.7 python-dev git libssl-dev libffi-dev build-essential libc6-dev-i386 docker.io

COPY ./scriptbot /opt/ictf/scriptbot
COPY ./common/teamhosts /etc/hosts

WORKDIR /opt/ictf/scriptbot

RUN pip install -r requirements.txt

RUN chmod +x ./start.sh 

ENTRYPOINT ./start.sh