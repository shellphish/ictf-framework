FROM ictf_3_cast_database

COPY ./database /opt/ictf/database
COPY ./scoring_ictf /opt/ictf/scoring_ictf

WORKDIR /opt/ictf/database

RUN chmod +x ./start.sh 

RUN ansible-playbook ./provisioning/ansible-provisioning.yml --extra-vars AWS_BUCKET_NAME="aws_bucket_name" --extra-vars AWS_REGION="aws_region" --extra-vars AWS_ACCESS_KEY="aws_access_key" --extra-vars AWS_SECRET_KEY="aws_secret_key"

ENTRYPOINT ./start.sh