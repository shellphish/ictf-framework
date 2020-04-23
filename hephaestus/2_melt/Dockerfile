FROM ictf_1_heat

RUN DEBIAN_FRONTEND=noninteractive apt-get -y -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" upgrade && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible 

RUN apt-get -y update && apt -y install ansible git wget curl vim

RUN mkdir -p /opt/ictf && chown -R $ICTF_USER:$ICTF_USER /opt/ictf

COPY ./secrets /opt/ictf/secrets
