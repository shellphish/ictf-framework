FROM ictf_2_melt

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-virtualenv python-dev nginx git redis-server build-essential nodejs npm sudo

COPY ./scoreboard /opt/ictf/scoreboard
COPY ./secrets /opt/ictf/secrets

WORKDIR /opt/ictf/scoreboard

RUN pip install -r requirements.txt

# RUN useradd -ms /bin/bash deploy

# USER deploy

# WORKDIR /home/deploy

# RUN curl -sL https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh -o install_nvm.sh && bash install_nvm.sh

RUN ansible-playbook --become --extra-vars ICTF_USER="hacker" --extra-vars ICTF_FRAMEWORK_DIR_HOST="/opt/ictf" provisioning/building_time/ansible/main.yml