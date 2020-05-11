FROM ictf_base

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y nginx uwsgi uwsgi-plugin-python mysql-server python-pip python-virtualenv python-mysqldb python-dev awscli openjdk-8-jdk openjdk-8-jdk-headless openjdk-8-jre
RUN pip install --upgrade pip setuptools pyOpenSSL ndg-httpsclient pyasn1

COPY ./database /opt/ictf/database
COPY ./scoring_ictf /opt/ictf/scoring_ictf

WORKDIR /opt/ictf/database

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/ansible-provisioning.yml --extra-vars AWS_BUCKET_NAME="aws_bucket_name" --extra-vars AWS_REGION="aws_region" --extra-vars AWS_ACCESS_KEY="aws_access_key" --extra-vars AWS_SECRET_KEY="aws_secret_key"

ENTRYPOINT ./start.sh